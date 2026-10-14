"""
tests/test_phase4_api.py
Suite de Pruebas de Integración HTTP de la FASE 4:
- Endpoint de Health Check
- GET /api/v1/dashboard/kpis (Métricas patrimoniales consolidadas)
- GET /api/v1/catalogos/maestros (Catálogos para selectores UI)
- GET /api/v1/integracion/empleados/{id}/activos-asignados (Custodia para RRHH)
- GET /api/v1/integracion/contabilidad/asiento-depreciacion (Asiento cuadrado Debe/Haber)
- POST /api/v1/activos/{id}/traslados (Validación de sedes)
- POST /api/v1/activos/{id}/mantenimientos (Registro de órdenes)
- GET /api/v1/reportes/ple-7-1 (Exportador normativo SUNAT .txt)
- GET /api/v1/alertas/vida-util y GET /api/v1/alertas/huerfanos
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.main import app
from backend.config.db_connection import get_engine
from backend.services.depreciation_service import calculate_and_close_monthly_depreciation

client = TestClient(app)


def test_health_check_endpoint():
    """Verifica que el servicio esté online y responda con diagnóstico de base de datos."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "ok"


def test_dashboard_kpis_endpoint():
    """Verifica que el endpoint de métricas devuelva los indicadores patrimoniales."""
    response = client.get("/api/v1/dashboard/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "total_activos_en_uso" in data
    assert "costo_historico_total" in data
    assert "depreciacion_acumulada_total" in data
    assert "valor_neto_en_libros_total" in data
    assert data["costo_patrimonial_total"] >= 0


def test_catalogos_maestros_endpoint():
    """Verifica el retorno de categorías, ubicaciones y empleados para la UI."""
    response = client.get("/api/v1/catalogos/maestros")
    assert response.status_code == 200
    data = response.json()
    assert len(data["categorias"]) >= 5
    assert len(data["ubicaciones"]) >= 1
    assert len(data["empleados"]) >= 1


def test_integracion_empleados_activos_asignados():
    """Verifica endpoint de entrega de activos en custodia para RRHH."""
    engine = get_engine()
    with engine.connect() as conn:
        emp_id = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()

    response = client.get(f"/api/v1/integracion/empleados/{emp_id}/activos-asignados")
    assert response.status_code == 200
    data = response.json()
    assert "empleado" in data
    assert "activos" in data
    assert "total_activos_en_custodia" in data
    assert data["empleado"]["id_empleado"] == emp_id

    resp_404 = client.get("/api/v1/integracion/empleados/999999/activos-asignados")
    assert resp_404.status_code == 404


def test_integracion_asiento_depreciacion():
    """Verifica que el asiento de diario contable esté cuadrado (Debe == Haber)."""
    calculate_and_close_monthly_depreciation(2026, 5, force_recalculate=True)

    response = client.get("/api/v1/integracion/contabilidad/asiento-depreciacion?anio=2026&mes=5")
    assert response.status_code == 200
    data = response.json()
    assert data["periodo"] == "2026-05"
    assert data["asiento_cuadrado"] is True
    assert data["total_debe"] == pytest.approx(data["total_haber"], 0.01)
    assert len(data["lineas_asiento"]) > 0

    for linea in data["lineas_asiento"]:
        if linea["debe"] > 0:
            assert linea["cuenta_codigo"].startswith("68")
        if linea["haber"] > 0:
            assert linea["cuenta_codigo"].startswith("39")


def test_traslado_activo_endpoint():
    """Verifica registro de traslado físico y validación de origen != destino."""
    engine = get_engine()
    with engine.connect() as conn:
        act_row = conn.execute(
            text("SELECT id_activo, id_ubicacion FROM activo_fijo WHERE id_estado = (SELECT id_estado FROM estado_activo WHERE nombre='EN_USO') LIMIT 1;")
        ).fetchone()
        id_act = act_row[0]
        id_ub_orig = act_row[1]

        id_ub_dest = conn.execute(
            text("SELECT id_ubicacion FROM ubicacion WHERE id_ubicacion <> :orig LIMIT 1;"),
            {"orig": id_ub_orig},
        ).scalar()
        emp_id = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()

    payload_invalido = {
        "id_ubicacion_destino": id_ub_orig,
        "motivo": "Intento de traslado a la misma sede",
        "id_autorizado_por": emp_id,
    }
    resp_fail = client.post(f"/api/v1/activos/{id_act}/traslados", json=payload_invalido)
    assert resp_fail.status_code == 400

    payload_valido = {
        "id_ubicacion_destino": id_ub_dest,
        "motivo": "Reasignación física a Data Center",
        "id_autorizado_por": emp_id,
    }
    resp_ok = client.post(f"/api/v1/activos/{id_act}/traslados", json=payload_valido)
    assert resp_ok.status_code == 200
    assert resp_ok.json()["status"] == "ok"
    assert resp_ok.json()["id_ubicacion_nueva"] == id_ub_dest


def test_mantenimiento_activo_endpoint():
    """Verifica registro de mantenimiento preventivo."""
    engine = get_engine()
    with engine.connect() as conn:
        id_act = conn.execute(text("SELECT id_activo FROM activo_fijo LIMIT 1;")).scalar()

    payload = {
        "tipo": "PREVENTIVO",
        "descripcion": "Limpieza interna, cambio de pasta térmica y calibración",
        "costo": 180.50,
    }
    resp = client.post(f"/api/v1/activos/{id_act}/mantenimientos", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["id_mantenimiento"] > 0


def test_reporte_ple_7_1_sunat():
    """Verifica exportación del archivo oficial PLE 7.1 según normativa SUNAT."""
    response = client.get("/api/v1/reportes/ple-7-1?anio=2026")
    assert response.status_code == 200
    assert "attachment; filename=LE" in response.headers["content-disposition"]
    assert response.headers["content-disposition"].endswith(".txt")

    content = response.text
    assert len(content) > 0
    lines = content.strip().split("\r\n")
    assert len(lines) > 0

    for line in lines:
        assert line.endswith("|")
        fields = line.split("|")
        assert len(fields) >= 35


def test_alertas_vida_util_y_huerfanos():
    """Verifica endpoints de monitoreo de vida útil y consistencia de activos."""
    resp_vu = client.get("/api/v1/alertas/vida-util")
    assert resp_vu.status_code == 200
    data_vu = resp_vu.json()
    assert "total_alertas" in data_vu
    assert "alertas" in data_vu

    resp_h = client.get("/api/v1/alertas/huerfanos")
    assert resp_h.status_code == 200
    data_h = resp_h.json()
    assert "total_huerfanos" in data_h
    assert "activos" in data_h

def test_preview_baja_endpoint():
    """Verifica endpoint de previsualizaci?n y c?lculo en tiempo real del impacto de baja."""
    resp_activos = client.get("/api/v1/activos?limit=1")
    assert resp_activos.status_code == 200
    activos = resp_activos.json().get("items", [])
    if activos:
        id_act = activos[0]["id_activo"]
        # Preview Obsolescencia
        resp_obs = client.get(f"/api/v1/activos/{id_act}/baja/preview?motivo=OBSOLESCENCIA")
        assert resp_obs.status_code == 200
        data_obs = resp_obs.json()
        assert data_obs["tipo_impacto"] == "PERDIDA"
        assert "vnl" in data_obs

        # Preview Venta con valor comercial
        resp_venta = client.get(f"/api/v1/activos/{id_act}/baja/preview?motivo=VENTA&valor_venta=50000")
        assert resp_venta.status_code == 200
        data_venta = resp_venta.json()
        assert data_venta["tipo_impacto"] in ["GANANCIA", "PERDIDA", "NEUTRO"]
