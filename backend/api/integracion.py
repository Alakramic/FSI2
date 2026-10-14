"""
backend/api/integracion.py
Endpoints de Integración Desacoplada del SGAF con otros módulos:
- Recursos Humanos: Custodia patrimonial y actas de entrega/no adeudo.
- Contabilidad General: Distribución del Asiento de Diario de Depreciación Mensual.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text
from backend.config.db_connection import get_engine

router = APIRouter(prefix="/integracion", tags=["Integración Empresarial"])


@router.get("/empleados/{id_empleado}/activos-asignados")
def get_activos_asignados_empleado(id_empleado: int):
    """
    Retorna el inventario de bienes en custodia activa de un empleado.
    Útil para actas de entrega o constancias de no adeudo en liquidaciones laborales.
    """
    engine = get_engine()
    with engine.connect() as conn:
        emp = conn.execute(
            text(
                """
                SELECT id_empleado, dni, nombres, apellidos, cargo, c.nombre AS centro_costo
                FROM empleado e
                JOIN centro_costo c ON e.id_centro_costo = c.id_centro_costo
                WHERE e.id_empleado = :id_emp;
                """
            ),
            {"id_emp": id_empleado},
        ).fetchone()

        if not emp:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró al empleado con ID: {id_empleado}",
            )

        activos = conn.execute(
            text(
                """
                SELECT 
                    a.id_activo,
                    a.codigo,
                    a.descripcion,
                    a.marca,
                    a.modelo,
                    a.numero_serie,
                    cat.nombre AS categoria,
                    u.nombre || ' (' || u.sede || ')' AS ubicacion,
                    asig.fecha_inicio AS fecha_asignacion,
                    asig.observacion
                FROM asignacion_activo asig
                JOIN activo_fijo a ON asig.id_activo = a.id_activo
                JOIN categoria_activo cat ON a.id_categoria = cat.id_categoria
                JOIN ubicacion u ON a.id_ubicacion = u.id_ubicacion
                JOIN estado_activo est ON a.id_estado = est.id_estado
                WHERE asig.id_empleado = :id_emp 
                  AND asig.fecha_fin IS NULL
                  AND est.nombre = 'EN_USO'
                ORDER BY asig.fecha_inicio DESC;
                """
            ),
            {"id_emp": id_empleado},
        ).fetchall()

    return {
        "empleado": {
            "id_empleado": emp[0],
            "dni": emp[1],
            "nombres": emp[2],
            "apellidos": emp[3],
            "cargo": emp[4],
            "centro_costo": emp[5],
        },
        "total_activos_en_custodia": len(activos),
        "activos": [
            {
                "id_activo": row[0],
                "codigo": row[1],
                "descripcion": row[2],
                "marca": row[3],
                "modelo": row[4],
                "numero_serie": row[5],
                "categoria": row[6],
                "ubicacion": row[7],
                "fecha_asignacion": str(row[8]),
                "observacion": row[9],
            }
            for row in activos
        ],
    }


@router.get("/contabilidad/asiento-depreciacion")
def get_asiento_depreciacion(
    anio: int = Query(..., description="Año contable YYYY"),
    mes: int = Query(..., ge=1, le=12, description="Mes contable 1 a 12"),
):
    """
    Retorna la distribución contable oficial para generar el asiento de Diario
    de depreciación devengada del periodo (Cuentas PCGE 68 al Debe y 39 al Haber).
    """
    engine = get_engine()
    with engine.connect() as conn:
        per = conn.execute(
            text("SELECT id_periodo, estado FROM periodo_contable WHERE anio = :a AND mes = :m;"),
            {"a": anio, "m": mes},
        ).fetchone()

        if not per:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se ha procesado depreciación para el periodo {anio}-{mes:02d}",
            )

        id_periodo = per[0]
        estado_periodo = per[1]

        # Agrupar cuotas por Cuenta de Gasto (Debe - Elemento 68) y Cuenta Depreciación (Haber - Elemento 39)
        filas = conn.execute(
            text(
                """
                SELECT 
                    cgasto.codigo AS cta_gasto_codigo,
                    cgasto.nombre AS cta_gasto_nombre,
                    cdep.codigo AS cta_dep_codigo,
                    cdep.nombre AS cta_dep_nombre,
                    cat.nombre AS categoria,
                    SUM(d.monto_periodo) AS total_cuota
                FROM depreciacion d
                JOIN activo_fijo a ON d.id_activo = a.id_activo
                JOIN categoria_activo cat ON a.id_categoria = cat.id_categoria
                JOIN cuenta_contable cgasto ON cat.id_cuenta_gasto = cgasto.id_cuenta
                JOIN cuenta_contable cdep ON cat.id_cuenta_dep_acum = cdep.id_cuenta
                WHERE d.id_periodo = :id_per AND d.monto_periodo > 0
                GROUP BY cgasto.codigo, cgasto.nombre, cdep.codigo, cdep.nombre, cat.nombre
                ORDER BY cdep.codigo ASC;
                """
            ),
            {"id_per": id_periodo},
        ).fetchall()

    lineas_debe = []
    lineas_haber = []
    total_debe = 0.0
    total_haber = 0.0

    for r in filas:
        monto = float(r[5])
        # Cuenta 68 (Debe)
        lineas_debe.append(
            {
                "cuenta_codigo": r[0],
                "cuenta_nombre": r[1],
                "glosa": f"Depreciación mensual {anio}-{mes:02d} - {r[4]}",
                "debe": monto,
                "haber": 0.0,
            }
        )
        # Cuenta 39 (Haber)
        lineas_haber.append(
            {
                "cuenta_codigo": r[2],
                "cuenta_nombre": r[3],
                "glosa": f"Depreciación acumulada {anio}-{mes:02d} - {r[4]}",
                "debe": 0.0,
                "haber": monto,
            }
        )
        total_debe += monto
        total_haber += monto

    return {
        "periodo": f"{anio}-{mes:02d}",
        "estado_periodo": estado_periodo,
        "asiento_cuadrado": round(total_debe, 2) == round(total_haber, 2),
        "total_debe": round(total_debe, 2),
        "total_haber": round(total_haber, 2),
        "lineas_asiento": lineas_debe + lineas_haber,
    }