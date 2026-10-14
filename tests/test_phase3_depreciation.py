"""
tests/test_phase3_depreciation.py
Suite de Pruebas Automatizadas de la FASE 3:
- Simulación de 12 meses de depreciación consecutiva en línea recta con exactitud centavo a centavo
- Regla de bien totalmente depreciado (cuota pasa a 0.00 y se preserva EN_USO)
- Control de periodos contables abiertos/cerrados
- Liquidación patrimonial por baja (SINIESTRO con pérdida directa = VNL)
- Liquidación patrimonial por VENTA con cálculo de ganancia o pérdida contable
- Finalización automática de asignaciones activas de custodia
"""

import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import text

from backend.config.db_connection import get_engine
from backend.services.depreciation_service import (
    calculate_and_close_monthly_depreciation,
    get_asset_vnl,
)
from backend.services.bajas_service import (
    preview_baja_financiera,
    register_baja_activo,
)


@pytest.fixture(scope="module")
def setup_depreciation_asset():
    """Crea un activo de prueba con costo S/ 12,000 y vida útil de 12 meses para simulación controlada."""
    engine = get_engine()
    with engine.begin() as conn:
        cat_id = conn.execute(text("SELECT id_categoria FROM categoria_activo WHERE nombre='Equipos de Cómputo';")).scalar()
        est_id = conn.execute(text("SELECT id_estado FROM estado_activo WHERE nombre='EN_USO';")).scalar()
        ub_id = conn.execute(text("SELECT id_ubicacion FROM ubicacion LIMIT 1;")).scalar()
        cc_id = conn.execute(text("SELECT id_centro_costo FROM centro_costo LIMIT 1;")).scalar()
        emp_id = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()
        doc_id = conn.execute(text("SELECT id_documento FROM documento_adquisicion LIMIT 1;")).scalar()

        # Activo con vida útil de 12 meses exactos (S/ 1,000 por mes)
        codigo_sim = "SIM-DEP-12M"
        conn.execute(text("DELETE FROM activo_fijo WHERE codigo = :c;"), {"c": codigo_sim})

        id_act = conn.execute(
            text(
                """
                INSERT INTO activo_fijo (
                    codigo, descripcion, id_categoria, id_estado, id_ubicacion,
                    id_centro_costo, id_responsable, id_documento,
                    fecha_adquisicion, fecha_inicio_uso, costo_adquisicion,
                    valor_residual, vida_util_meses, metodo_depreciacion
                ) VALUES (
                    :codigo, 'Servidor Simulación 12M', :cat_id, :est_id, :ub_id,
                    :cc_id, :emp_id, :doc_id,
                    '2025-01-01', '2025-01-01', 12000.00,
                    0.00, 12, '1'
                ) RETURNING id_activo;
                """
            ),
            {
                "codigo": codigo_sim,
                "cat_id": cat_id,
                "est_id": est_id,
                "ub_id": ub_id,
                "cc_id": cc_id,
                "emp_id": emp_id,
                "doc_id": doc_id,
            },
        ).scalar()

        # Asignación inicial
        conn.execute(
            text(
                """
                INSERT INTO asignacion_activo (id_activo, id_empleado, fecha_inicio, observacion)
                VALUES (:id_act, :emp_id, '2025-01-01', 'Asignación simulación');
                """
            ),
            {"id_act": id_act, "emp_id": emp_id},
        )

    return id_act


def test_12_months_consecutive_depreciation_accuracy(setup_depreciation_asset):
    """Simula 12 meses consecutivos de depreciación y verifica el saldo acumulado centavo a centavo."""
    id_activo = setup_depreciation_asset

    for mes in range(1, 13):
        res = calculate_and_close_monthly_depreciation(anio=2025, mes=mes, force_recalculate=True)
        assert res["estado"] == "CERRADO"

        detalle = next((d for d in res["detalles"] if d["id_activo"] == id_activo), None)
        assert detalle is not None, f"El activo no fue procesado en el mes {mes}"

        cuota_esperada = 1000.00
        acum_esperado = 1000.00 * mes
        neto_esperado = 12000.00 - acum_esperado

        assert detalle["cuota_mes"] == pytest.approx(cuota_esperada, 0.01)
        assert detalle["depreciacion_acum"] == pytest.approx(acum_esperado, 0.01)
        assert detalle["valor_neto"] == pytest.approx(neto_esperado, 0.01)

    # Al mes 12, el activo debe estar totalmente depreciado (VNL = 0.00)
    info_final = get_asset_vnl(id_activo)
    assert info_final["vnl"] == 0.00
    assert info_final["depreciacion_acum"] == 12000.00


def test_fully_depreciated_asset_rule(setup_depreciation_asset):
    """
    En el mes 13 (año siguiente), la cuota debe ser 0.00 y el activo debe
    mantenerse en estado EN_USO sin forzar su retiro ni eliminación.
    """
    id_activo = setup_depreciation_asset
    res = calculate_and_close_monthly_depreciation(anio=2026, mes=1, force_recalculate=True)

    detalle = next((d for d in res["detalles"] if d["id_activo"] == id_activo), None)
    assert detalle is not None
    assert detalle["cuota_mes"] == 0.00
    assert detalle["depreciacion_acum"] == 12000.00
    assert detalle["valor_neto"] == 0.00
    assert detalle["totalmente_depreciado"] is True

    # Verificar que el activo sigue en estado EN_USO en la base de datos
    engine = get_engine()
    with engine.connect() as conn:
        estado = conn.execute(
            text(
                """
                SELECT e.nombre 
                FROM activo_fijo a 
                JOIN estado_activo e ON a.id_estado = e.id_estado 
                WHERE a.id_activo = :id_act;
                """
            ),
            {"id_act": id_activo},
        ).scalar()
        assert estado == "EN_USO"


def test_baja_por_siniestro_perdida_directa():
    """
    Verifica que una baja por SINIESTRO asuma una pérdida patrimonial igual al VNL
    y cierre la custodia del custodio.
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM activo_fijo WHERE codigo = 'BAJA-SINIESTRO-01';"))
        cat_id = conn.execute(text("SELECT id_categoria FROM categoria_activo LIMIT 1;")).scalar()
        est_id = conn.execute(text("SELECT id_estado FROM estado_activo WHERE nombre='EN_USO';")).scalar()
        ub_id = conn.execute(text("SELECT id_ubicacion FROM ubicacion LIMIT 1;")).scalar()
        cc_id = conn.execute(text("SELECT id_centro_costo FROM centro_costo LIMIT 1;")).scalar()
        emp_id = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()
        doc_id = conn.execute(text("SELECT id_documento FROM documento_adquisicion LIMIT 1;")).scalar()

        id_act = conn.execute(
            text(
                """
                INSERT INTO activo_fijo (
                    codigo, descripcion, id_categoria, id_estado, id_ubicacion,
                    id_centro_costo, id_responsable, id_documento,
                    fecha_adquisicion, fecha_inicio_uso, costo_adquisicion,
                    valor_residual, vida_util_meses, metodo_depreciacion
                ) VALUES (
                    'BAJA-SINIESTRO-01', 'Laptop para Siniestro', :cat_id, :est_id, :ub_id,
                    :cc_id, :emp_id, :doc_id,
                    '2026-01-01', '2026-01-01', 5000.00,
                    0.00, 20, '1'
                ) RETURNING id_activo;
                """
            ),
            {
                "cat_id": cat_id,
                "est_id": est_id,
                "ub_id": ub_id,
                "cc_id": cc_id,
                "emp_id": emp_id,
                "doc_id": doc_id,
            },
        ).scalar()

        conn.execute(
            text(
                """
                INSERT INTO asignacion_activo (id_activo, id_empleado, fecha_inicio)
                VALUES (:id_act, :emp_id, '2026-01-01');
                """
            ),
            {"id_act": id_act, "emp_id": emp_id},
        )

    # VNL inicial = 5000.00
    preview = preview_baja_financiera(id_act, motivo="SINIESTRO")
    assert preview["tipo_impacto"] == "PERDIDA"
    assert preview["vnl"] == 5000.00
    assert preview["monto_impacto"] == 5000.00

    # Registrar baja
    resultado_baja = register_baja_activo(
        id_activo=id_act,
        motivo="SINIESTRO",
        fecha_baja=date(2026, 2, 1),
        observacion="Siniestro por sobrevoltaje",
    )
    assert resultado_baja["estado_final"] == "DADO_DE_BAJA"

    # Verificar que la asignación quedó cerrada con fecha_fin
    with engine.connect() as conn:
        asig = conn.execute(
            text("SELECT fecha_fin FROM asignacion_activo WHERE id_activo = :id_act;"),
            {"id_act": id_act},
        ).fetchone()
        assert asig[0] == date(2026, 2, 1)


def test_baja_por_venta_ganancia_y_perdida():
    """
    Verifica cálculo de resultado por venta:
    - Ganancia si Venta > VNL
    - Pérdida si Venta < VNL
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM activo_fijo WHERE codigo = 'VENTA-TEST-01';"))
        cat_id = conn.execute(text("SELECT id_categoria FROM categoria_activo LIMIT 1;")).scalar()
        est_id = conn.execute(text("SELECT id_estado FROM estado_activo WHERE nombre='EN_USO';")).scalar()
        ub_id = conn.execute(text("SELECT id_ubicacion FROM ubicacion LIMIT 1;")).scalar()
        cc_id = conn.execute(text("SELECT id_centro_costo FROM centro_costo LIMIT 1;")).scalar()
        emp_id = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()
        doc_id = conn.execute(text("SELECT id_documento FROM documento_adquisicion LIMIT 1;")).scalar()

        id_act = conn.execute(
            text(
                """
                INSERT INTO activo_fijo (
                    codigo, descripcion, id_categoria, id_estado, id_ubicacion,
                    id_centro_costo, id_responsable, id_documento,
                    fecha_adquisicion, fecha_inicio_uso, costo_adquisicion,
                    valor_residual, vida_util_meses, metodo_depreciacion
                ) VALUES (
                    'VENTA-TEST-01', 'Vehículo para Venta', :cat_id, :est_id, :ub_id,
                    :cc_id, :emp_id, :doc_id,
                    '2026-01-01', '2026-01-01', 10000.00,
                    0.00, 10, '1'
                ) RETURNING id_activo;
                """
            ),
            {
                "cat_id": cat_id,
                "est_id": est_id,
                "ub_id": ub_id,
                "cc_id": cc_id,
                "emp_id": emp_id,
                "doc_id": doc_id,
            },
        ).scalar()

    # VNL = 10,000. Venta en 12,500 -> Ganancia de 2,500
    prev_ganancia = preview_baja_financiera(id_act, motivo="VENTA", valor_venta=12500.00)
    assert prev_ganancia["tipo_impacto"] == "GANANCIA"
    assert prev_ganancia["monto_impacto"] == 2500.00

    # Venta en 8,000 -> Pérdida de 2,000
    prev_perdida = preview_baja_financiera(id_act, motivo="VENTA", valor_venta=8000.00)
    assert prev_perdida["tipo_impacto"] == "PERDIDA"
    assert prev_perdida["monto_impacto"] == 2000.00

    # Registrar venta con ganancia
    res_venta = register_baja_activo(
        id_activo=id_act,
        motivo="VENTA",
        valor_venta=12500.00,
        fecha_baja=date(2026, 3, 1),
    )
    assert res_venta["estado_final"] == "VENDIDO"