"""
backend/services/bajas_service.py
Gestión Financiera y Patrimonial de Bajas, Siniestros y Enajenaciones (SGAF).
Calcula pérdidas contables directas o ganancias por venta según el VNL,
finaliza custodias activas y actualiza los catálogos normativos SUNAT.
"""

from typing import Dict, Any, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy import text
from backend.config.db_connection import get_engine
from backend.services.depreciation_service import get_asset_vnl


MOTIVOS_VALIDOS = ["OBSOLESCENCIA", "ROBO", "SINIESTRO", "VENTA", "DONACION"]


def preview_baja_financiera(
    id_activo: int,
    motivo: str,
    valor_venta: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calcula el impacto contable previo a la confirmación de la baja.
    """
    motivo_upper = motivo.strip().upper()
    if motivo_upper not in MOTIVOS_VALIDOS:
        raise ValueError(f"Motivo inválido '{motivo}'. Debe ser uno de: {', '.join(MOTIVOS_VALIDOS)}")

    info_vnl = get_asset_vnl(id_activo)
    vnl = Decimal(str(info_vnl["vnl"]))

    if motivo_upper == "VENTA":
        if valor_venta is None or valor_venta < 0:
            raise ValueError("Para bajas por VENTA se requiere especificar un valor_venta válido (>= 0).")
        venta = Decimal(str(valor_venta))
        resultado = venta - vnl
        if resultado > Decimal("0.00"):
            tipo_impacto = "GANANCIA"
            mensaje = f"Se registrará una ganancia contable por enajenación de S/ {resultado:,.2f}"
        elif resultado < Decimal("0.00"):
            tipo_impacto = "PERDIDA"
            mensaje = f"Se registrará una pérdida contable por enajenación de S/ {abs(resultado):,.2f}"
        else:
            tipo_impacto = "NEUTRO"
            mensaje = "El valor de venta es igual al VNL (impacto neutro en resultados)."
        monto_impacto = abs(resultado)
    else:
        # Obsolescencia, Robo, Siniestro, Donación
        venta = None
        tipo_impacto = "PERDIDA"
        monto_impacto = vnl
        mensaje = f"Se asumirá como pérdida patrimonial directa el VNL de S/ {vnl:,.2f}"

    return {
        "id_activo": id_activo,
        "codigo": info_vnl["codigo"],
        "descripcion": info_vnl["descripcion"],
        "costo_adquisicion": info_vnl["costo_adquisicion"],
        "depreciacion_acumulada": info_vnl["depreciacion_acum"],
        "vnl": float(vnl),
        "motivo": motivo_upper,
        "valor_venta": float(venta) if venta is not None else None,
        "tipo_impacto": tipo_impacto,
        "monto_impacto": float(monto_impacto),
        "mensaje": mensaje,
    }


def register_baja_activo(
    id_activo: int,
    motivo: str,
    fecha_baja: Optional[date] = None,
    valor_venta: Optional[float] = None,
    observacion: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ejecuta la baja atómica del bien patrimonial:
    1. Calcula el VNL a la fecha.
    2. Inserta el registro en baja_activo.
    3. Cambia el estado del activo a DADO_DE_BAJA o VENDIDO y estado_activo_ple a '8'.
    4. Cierra las asignaciones activas de custodios.
    """
    engine = get_engine()
    preview = preview_baja_financiera(id_activo, motivo, valor_venta)
    fecha = fecha_baja or date.today()
    obs = observacion or f"Baja patrimonial por {preview['motivo']}"

    with engine.begin() as conn:
        # Verificar si ya tiene baja registrada
        baja_exists = conn.execute(
            text("SELECT 1 FROM baja_activo WHERE id_activo = :id_act;"),
            {"id_act": id_activo},
        ).scalar()

        if baja_exists:
            raise ValueError(f"El activo con ID {id_activo} ya fue dado de baja previamente.")

        # Obtener nuevo estado
        nombre_estado = "VENDIDO" if preview["motivo"] == "VENTA" else "DADO_DE_BAJA"
        id_nuevo_estado = conn.execute(
            text("SELECT id_estado FROM estado_activo WHERE nombre = :nom;"),
            {"nom": nombre_estado},
        ).scalar()

        # 1. Insertar en baja_activo
        conn.execute(
            text(
                """
                INSERT INTO baja_activo (id_activo, fecha, motivo, valor_libros, valor_venta, observacion)
                VALUES (:id_act, :fecha, :motivo, :vnl, :venta, :obs);
                """
            ),
            {
                "id_act": id_activo,
                "fecha": fecha,
                "motivo": preview["motivo"],
                "vnl": preview["vnl"],
                "venta": preview["valor_venta"],
                "obs": obs,
            },
        )

        # 2. Actualizar activo_fijo
        conn.execute(
            text(
                """
                UPDATE activo_fijo 
                SET id_estado = :id_est,
                    estado_activo_ple = '8'
                WHERE id_activo = :id_act;
                """
            ),
            {"id_est": id_nuevo_estado, "id_act": id_activo},
        )

        # 3. Finalizar asignaciones activas
        conn.execute(
            text(
                """
                UPDATE asignacion_activo 
                SET fecha_fin = :fecha,
                    observacion = COALESCE(observacion, '') || ' [Cerrado por baja de activo]'
                WHERE id_activo = :id_act AND fecha_fin IS NULL;
                """
            ),
            {"fecha": fecha, "id_act": id_activo},
        )

    return {
        **preview,
        "fecha_baja": str(fecha),
        "estado_final": nombre_estado,
        "observacion": obs,
    }