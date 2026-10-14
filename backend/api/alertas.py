"""
backend/api/alertas.py
Endpoints de Monitoreo Preventivo y Auditoría Patrimonial:
- Alertas de expiración de vida útil contable (a 60 y 30 días de culminar).
- Detección de activos huérfanos (bienes activos sin custodio o sin sede asignada).
"""

from typing import List, Dict, Any
from datetime import date
from fastapi import APIRouter
from sqlalchemy import text
from backend.config.db_connection import get_engine

router = APIRouter(prefix="/alertas", tags=["Monitoreo y Alertas"])


@router.get("/vida-util")
def get_alertas_vida_util():
    """
    Identifica activos en uso próximos a culminar su vida útil contable:
    - Crítica: Culminación en <= 1 mes (30 días).
    - Preventiva: Culminación en <= 2 meses (60 días).
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT 
                    a.id_activo,
                    a.codigo,
                    a.descripcion,
                    cat.nombre AS categoria,
                    a.fecha_inicio_uso,
                    a.vida_util_meses,
                    COALESCE(SUM(m.meses_vida_adicional), 0) AS meses_extra,
                    COALESCE(dep_info.meses_depreciados, 0) AS meses_depreciados,
                    COALESCE(dep_info.vnl, a.costo_adquisicion) AS vnl
                FROM activo_fijo a
                JOIN categoria_activo cat ON a.id_categoria = cat.id_categoria
                JOIN estado_activo est ON a.id_estado = est.id_estado
                LEFT JOIN mejora_activo m ON a.id_activo = m.id_activo
                LEFT JOIN LATERAL (
                    SELECT 
                        COUNT(d.id_depreciacion) AS meses_depreciados,
                        MIN(d.valor_neto) AS vnl
                    FROM depreciacion d
                    WHERE d.id_activo = a.id_activo
                ) dep_info ON true
                WHERE est.nombre = 'EN_USO'
                GROUP BY a.id_activo, a.codigo, a.descripcion, cat.nombre,
                         a.fecha_inicio_uso, a.vida_util_meses, dep_info.meses_depreciados,
                         dep_info.vnl, a.costo_adquisicion
                ORDER BY a.id_activo ASC;
                """
            )
        ).fetchall()

    alertas = []
    for r in rows:
        vida_util_total = int(r[5]) + int(r[6])
        meses_dep = int(r[7])
        meses_restantes = vida_util_total - meses_dep

        # Alertas a 60 días (<= 2 meses) y 30 días (<= 1 mes)
        if 0 < meses_restantes <= 2:
            nivel = "CRITICA_30_DIAS" if meses_restantes <= 1 else "PREVENTIVA_60_DIAS"
            alertas.append(
                {
                    "id_activo": r[0],
                    "codigo": r[1],
                    "descripcion": r[2],
                    "categoria": r[3],
                    "nivel_alerta": nivel,
                    "meses_restantes": meses_restantes,
                    "dias_estimados": meses_restantes * 30,
                    "vnl_actual": float(r[8]),
                }
            )

    return {
        "total_alertas": len(alertas),
        "alertas": alertas,
    }


@router.get("/huerfanos")
def get_alertas_huerfanos():
    """
    Detecta inconsistencias operativas: activos patrimoniales en uso
    que carecen de custodio responsable o no tienen ubicación física asignada.
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT 
                    a.id_activo,
                    a.codigo,
                    a.descripcion,
                    a.costo_adquisicion,
                    cat.nombre AS categoria,
                    a.id_responsable,
                    a.id_ubicacion,
                    CASE 
                        WHEN a.id_responsable IS NULL AND a.id_ubicacion IS NULL THEN 'SIN_CUSTODIO_Y_SIN_UBICACION'
                        WHEN a.id_responsable IS NULL THEN 'SIN_CUSTODIO'
                        WHEN a.id_ubicacion IS NULL THEN 'SIN_UBICACION'
                        ELSE 'ASIGNACION_DESACTUALIZADA'
                    END AS tipo_inconsistencia
                FROM activo_fijo a
                JOIN categoria_activo cat ON a.id_categoria = cat.id_categoria
                JOIN estado_activo est ON a.id_estado = est.id_estado
                LEFT JOIN asignacion_activo asig ON a.id_activo = asig.id_activo AND asig.fecha_fin IS NULL
                WHERE est.nombre = 'EN_USO'
                  AND (a.id_responsable IS NULL OR a.id_ubicacion IS NULL OR asig.id_asignacion IS NULL);
                """
            )
        ).fetchall()

    return {
        "total_huerfanos": len(rows),
        "activos": [
            {
                "id_activo": r[0],
                "codigo": r[1],
                "descripcion": r[2],
                "costo": float(r[3]),
                "categoria": r[4],
                "motivo": r[7],
            }
            for r in rows
        ],
    }