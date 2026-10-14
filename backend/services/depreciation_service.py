"""
backend/services/depreciation_service.py
Motor Contable de Depreciación Mensual en Línea Recta (SGAF).
Implementa devengo mensual, control de periodos contables abiertos/cerrados,
capitalización de mejoras, cálculo exacto de centavos y preservación de
activos totalmente depreciados en estado EN_USO.
"""

from typing import Dict, Any, List, Optional
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import calendar
from sqlalchemy import text
from backend.config.db_connection import get_engine


def _round_currency(value: Decimal) -> Decimal:
    """Asegura redondeo financiero exacto a 2 decimales (ROUND_HALF_UP)."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_or_create_periodo(conn, anio: int, mes: int) -> Dict[str, Any]:
    """Obtiene o crea un periodo contable (anio, mes)."""
    if not (1 <= mes <= 12):
        raise ValueError(f"Mes contable inválido: {mes}. Debe estar entre 1 y 12.")

    row = conn.execute(
        text("SELECT id_periodo, anio, mes, estado FROM periodo_contable WHERE anio = :a AND mes = :m;"),
        {"a": anio, "m": mes},
    ).fetchone()

    if row:
        return {"id_periodo": row[0], "anio": row[1], "mes": row[2], "estado": row[3]}

    id_per = conn.execute(
        text(
            """
            INSERT INTO periodo_contable (anio, mes, estado)
            VALUES (:a, :m, 'ABIERTO')
            RETURNING id_periodo;
            """
        ),
        {"a": anio, "m": mes},
    ).scalar()

    return {"id_periodo": id_per, "anio": anio, "mes": mes, "estado": "ABIERTO"}


def calculate_and_close_monthly_depreciation(
    anio: int,
    mes: int,
    force_recalculate: bool = False,
) -> Dict[str, Any]:
    """
    Ejecuta el cierre mensual de depreciación para el periodo (anio, mes)
    de forma atómica y secuencial en PostgreSQL.
    """
    engine = get_engine()

    with engine.begin() as conn:
        periodo = get_or_create_periodo(conn, anio, mes)
        id_periodo = periodo["id_periodo"]

        # Si el periodo ya está cerrado y no se fuerza recálculo, rechazar
        if periodo["estado"] == "CERRADO" and not force_recalculate:
            raise ValueError(
                f"El periodo contable {anio}-{mes:02d} ya se encuentra CERRADO. "
                "Para recalcular debe abrirse o utilizar force_recalculate=True."
            )

        # Si ya existen registros de este periodo y se fuerza, limpiarlos
        conn.execute(
            text("DELETE FROM depreciacion WHERE id_periodo = :id_per;"),
            {"id_per": id_periodo},
        )

        # Fecha de corte: último día del mes
        _, last_day = calendar.monthrange(anio, mes)
        fecha_corte = date(anio, mes, last_day)

        # Obtener todos los activos que iniciaron uso antes o durante este periodo
        # y que se encuentren en estado EN_USO (o que fueron dados de baja DESPUÉS de este periodo)
        activos = conn.execute(
            text(
                """
                SELECT 
                    a.id_activo,
                    a.codigo,
                    a.descripcion,
                    a.costo_adquisicion,
                    a.valor_residual,
                    a.vida_util_meses,
                    a.fecha_inicio_uso,
                    e.nombre AS estado_nombre,
                    COALESCE(SUM(m.monto), 0) AS total_mejoras,
                    COALESCE(SUM(m.meses_vida_adicional), 0) AS meses_adicionales
                FROM activo_fijo a
                JOIN estado_activo e ON a.id_estado = e.id_estado
                LEFT JOIN mejora_activo m ON a.id_activo = m.id_activo AND m.fecha <= :fecha_corte
                WHERE a.fecha_inicio_uso <= :fecha_corte
                  AND (e.nombre = 'EN_USO' OR a.id_activo IN (
                      -- Si fue dado de baja después de este mes, todavía deprecia en este mes
                      SELECT id_activo FROM baja_activo WHERE fecha > :fecha_corte
                  ))
                GROUP BY a.id_activo, a.codigo, a.descripcion, a.costo_adquisicion, 
                         a.valor_residual, a.vida_util_meses, a.fecha_inicio_uso, e.nombre
                ORDER BY a.id_activo ASC;
                """
            ),
            {"fecha_corte": fecha_corte},
        ).fetchall()

        detalles_depreciacion: List[Dict[str, Any]] = []
        total_cuota_mes = Decimal("0.00")

        for act in activos:
            id_activo = act[0]
            codigo = act[1]
            desc = act[2]
            costo_orig = Decimal(str(act[3]))
            val_residual = Decimal(str(act[4]))
            vida_util_orig = int(act[5])
            fecha_uso = act[6]
            estado_nom = act[7]
            mejoras_monto = Decimal(str(act[8]))
            meses_extra = int(act[9])

            vida_util_total = vida_util_orig + meses_extra
            base_depreciable = (costo_orig + mejoras_monto) - val_residual

            if base_depreciable < Decimal("0.00"):
                base_depreciable = Decimal("0.00")

            # Buscar última depreciación acumulada anterior a este periodo
            prev_dep_row = conn.execute(
                text(
                    """
                    SELECT d.depreciacion_acum
                    FROM depreciacion d
                    JOIN periodo_contable p ON d.id_periodo = p.id_periodo
                    WHERE d.id_activo = :id_act
                      AND (p.anio < :anio OR (p.anio = :anio AND p.mes < :mes))
                    ORDER BY p.anio DESC, p.mes DESC
                    LIMIT 1;
                    """
                ),
                {"id_act": id_activo, "anio": anio, "mes": mes},
            ).fetchone()

            dep_acum_previa = Decimal(str(prev_dep_row[0])) if prev_dep_row else Decimal("0.00")

            # Remanente por depreciar
            remanente_depreciable = base_depreciable - dep_acum_previa

            # Regla de bien totalmente depreciado:
            # Si el remanente es <= 0, cuota mensual es 0.00 y se preserva el bien
            if remanente_depreciable <= Decimal("0.00"):
                cuota_mes = Decimal("0.00")
                dep_acum_actual = dep_acum_previa
            else:
                # Cuota teórica mensual en línea recta
                cuota_teorica = _round_currency(base_depreciable / Decimal(vida_util_total))
                if cuota_teorica > remanente_depreciable:
                    cuota_mes = remanente_depreciable
                else:
                    cuota_mes = cuota_teorica
                dep_acum_actual = dep_acum_previa + cuota_mes

            # Valor Neto en Libros (VNL) = Costo total - Depreciación Acumulada
            costo_total = costo_orig + mejoras_monto
            valor_neto = _round_currency(costo_total - dep_acum_actual)

            # Insertar en tabla depreciacion
            conn.execute(
                text(
                    """
                    INSERT INTO depreciacion (id_activo, id_periodo, monto_periodo, depreciacion_acum, valor_neto)
                    VALUES (:id_act, :id_per, :monto, :acum, :neto);
                    """
                ),
                {
                    "id_act": id_activo,
                    "id_per": id_periodo,
                    "monto": cuota_mes,
                    "acum": dep_acum_actual,
                    "neto": valor_neto,
                },
            )

            total_cuota_mes += cuota_mes
            detalles_depreciacion.append(
                {
                    "id_activo": id_activo,
                    "codigo": codigo,
                    "descripcion": desc,
                    "cuota_mes": float(cuota_mes),
                    "depreciacion_acum": float(dep_acum_actual),
                    "valor_neto": float(valor_neto),
                    "totalmente_depreciado": (remanente_depreciable <= Decimal("0.00")),
                }
            )

        # Bloquear y cerrar el periodo contable
        conn.execute(
            text("UPDATE periodo_contable SET estado = 'CERRADO' WHERE id_periodo = :id_per;"),
            {"id_per": id_periodo},
        )

    return {
        "id_periodo": id_periodo,
        "anio": anio,
        "mes": mes,
        "estado": "CERRADO",
        "activos_procesados": len(detalles_depreciacion),
        "total_depreciacion_mes": float(total_cuota_mes),
        "detalles": detalles_depreciacion,
    }


def get_asset_vnl(id_activo: int, conn=None) -> Dict[str, Any]:
    """Calcula y retorna el Valor Neto en Libros (VNL) más reciente de un activo."""
    def _execute_query(connection):
        row = connection.execute(
            text(
                """
                SELECT 
                    a.id_activo,
                    a.codigo,
                    a.descripcion,
                    a.costo_adquisicion,
                    a.valor_residual,
                    COALESCE(SUM(m.monto), 0) AS mejoras,
                    COALESCE(d.depreciacion_acum, 0) AS dep_acum,
                    COALESCE(d.valor_neto, a.costo_adquisicion) AS valor_neto
                FROM activo_fijo a
                LEFT JOIN mejora_activo m ON a.id_activo = m.id_activo
                LEFT JOIN LATERAL (
                    SELECT dep.depreciacion_acum, dep.valor_neto
                    FROM depreciacion dep
                    JOIN periodo_contable p ON dep.id_periodo = p.id_periodo
                    WHERE dep.id_activo = a.id_activo
                    ORDER BY p.anio DESC, p.mes DESC
                    LIMIT 1
                ) d ON true
                WHERE a.id_activo = :id_act
                GROUP BY a.id_activo, a.codigo, a.descripcion, a.costo_adquisicion, 
                         a.valor_residual, d.depreciacion_acum, d.valor_neto;
                """
            ),
            {"id_act": id_activo},
        ).fetchone()

        if not row:
            raise ValueError(f"No existe el activo con ID: {id_activo}")

        costo_adq = Decimal(str(row[3]))
        val_res = Decimal(str(row[4]))
        mejoras = Decimal(str(row[5]))
        dep_acum = Decimal(str(row[6]))
        costo_total = costo_adq + mejoras
        vnl = _round_currency(costo_total - dep_acum)

        return {
            "id_activo": row[0],
            "codigo": row[1],
            "descripcion": row[2],
            "costo_adquisicion": float(costo_adq),
            "mejoras": float(mejoras),
            "costo_total": float(costo_total),
            "depreciacion_acum": float(dep_acum),
            "vnl": float(vnl),
            "valor_residual": float(val_res),
        }

    if conn is not None:
        return _execute_query(conn)

    engine = get_engine()
    with engine.connect() as connection:
        return _execute_query(connection)