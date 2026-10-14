"""
backend/api/dashboard.py
Endpoints para Métricas y KPIs Patrimoniales del Dashboard Principal.
"""

from fastapi import APIRouter
from sqlalchemy import text
from backend.config.db_connection import get_engine

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis")
def get_dashboard_kpis():
    """Retorna los indicadores patrimoniales y contables globales para el Dashboard."""
    engine = get_engine()
    with engine.connect() as conn:
        # 1. Total activos activos y costo histórico
        row_activos = conn.execute(
            text(
                """
                SELECT 
                    COUNT(a.id_activo) AS total_activos,
                    COALESCE(SUM(a.costo_adquisicion), 0) AS costo_historico_total,
                    COALESCE(SUM(a.valor_residual), 0) AS valor_residual_total
                FROM activo_fijo a
                JOIN estado_activo est ON a.id_estado = est.id_estado
                WHERE est.nombre = 'EN_USO';
                """
            )
        ).fetchone()

        total_activos = row_activos[0]
        costo_historico = float(row_activos[1])
        valor_residual = float(row_activos[2])

        # 2. Total mejoras capitalizadas
        mejoras_total = conn.execute(
            text("SELECT COALESCE(SUM(monto), 0) FROM mejora_activo;")
        ).scalar()
        mejoras_total = float(mejoras_total or 0)

        # 3. Depreciación acumulada total más reciente de activos en uso
        dep_acum_total = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(d_last.depreciacion_acum), 0)
                FROM activo_fijo a
                JOIN estado_activo est ON a.id_estado = est.id_estado
                LEFT JOIN LATERAL (
                    SELECT dep.depreciacion_acum
                    FROM depreciacion dep
                    JOIN periodo_contable p ON dep.id_periodo = p.id_periodo
                    WHERE dep.id_activo = a.id_activo
                    ORDER BY p.anio DESC, p.mes DESC
                    LIMIT 1
                ) d_last ON true
                WHERE est.nombre = 'EN_USO';
                """
            )
        ).scalar()
        dep_acum_total = float(dep_acum_total or 0)

        # 4. Valor Neto en Libros actual
        costo_patrimonial_total = costo_historico + mejoras_total
        vnl_total = round(costo_patrimonial_total - dep_acum_total, 2)

        # 5. Último periodo contable cerrado y su depreciación
        ultimo_periodo = conn.execute(
            text(
                """
                SELECT p.anio, p.mes, COALESCE(SUM(d.monto_periodo), 0)
                FROM periodo_contable p
                LEFT JOIN depreciacion d ON p.id_periodo = d.id_periodo
                WHERE p.estado = 'CERRADO'
                GROUP BY p.anio, p.mes
                ORDER BY p.anio DESC, p.mes DESC
                LIMIT 1;
                """
            )
        ).fetchone()

        if ultimo_periodo:
            periodo_label = f"{ultimo_periodo[0]}-{ultimo_periodo[1]:02d}"
            depreciacion_ultimo_mes = float(ultimo_periodo[2])
        else:
            periodo_label = "Sin cierres"
            depreciacion_ultimo_mes = 0.0

        # 6. Alertas
        bajas_total = conn.execute(text("SELECT COUNT(*) FROM baja_activo;")).scalar() or 0

    return {
        "total_activos_en_uso": total_activos,
        "costo_historico_total": costo_historico,
        "mejoras_capitalizadas": mejoras_total,
        "costo_patrimonial_total": costo_patrimonial_total,
        "depreciacion_acumulada_total": dep_acum_total,
        "valor_neto_en_libros_total": vnl_total,
        "ultimo_periodo_cerrado": periodo_label,
        "depreciacion_ultimo_mes": depreciacion_ultimo_mes,
        "total_bajas_historicas": bajas_total,
    }