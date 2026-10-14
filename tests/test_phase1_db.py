"""
tests/test_phase1_db.py
Suite de Pruebas Automatizadas de la FASE 1:
- Abstracción semántica del esquema (TABLES y COLUMNS)
- Conexión y diagnóstico multi-perfil
- Existencia e integridad de las 17 tablas relacionales en PostgreSQL
- Catálogos base y semillero (PCGE, estados, categorías)
- Integridad referencial (FKs) y restricciones CHECK / UNIQUE
"""

import pytest
from datetime import date
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.config.db_schema import TABLES, COLUMNS, t, col
from backend.config.db_connection import ping_db, get_engine, get_active_profile


def test_schema_constants_completeness():
    """Verifica que las 17 tablas del SGAF estén declaradas en TABLES y COLUMNS."""
    assert len(TABLES) == 17, f"Se esperaban 17 tablas en TABLES, pero hay {len(TABLES)}"
    
    expected_tables = {
        "CUENTA_CONTABLE", "CATEGORIA_ACTIVO", "UBICACION", "CENTRO_COSTO",
        "PROVEEDOR", "EMPLEADO", "ESTADO_ACTIVO", "DOCUMENTO_ADQUISICION",
        "ACTIVO_FIJO", "ASIGNACION_ACTIVO", "TRASLADO_ACTIVO", "MANTENIMIENTO",
        "MEJORA_ACTIVO", "REVALUACION", "BAJA_ACTIVO", "PERIODO_CONTABLE", "DEPRECIACION"
    }
    assert set(TABLES.keys()) == expected_tables

    for table_key in expected_tables:
        assert table_key in COLUMNS, f"Faltan columnas definidas para {table_key}"
        assert len(COLUMNS[table_key]) > 0, f"Tabla {table_key} no tiene columnas configuradas"


def test_database_connection_and_ping():
    """Valida conectividad con PostgreSQL y diagnóstico de latencia."""
    diag = ping_db()
    assert diag["status"] == "ok"
    assert diag["profile"] == get_active_profile()
    assert "PostgreSQL" in diag["version"]
    assert diag["latency_ms"] >= 0


def test_all_17_tables_exist_in_postgresql():
    """Verifica que todas las 17 tablas físicas existan en el esquema public de PostgreSQL."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
                """
            )
        )
        existing_tables = {row[0] for row in result.fetchall()}

    for key, table_name in TABLES.items():
        assert table_name in existing_tables, f"La tabla {table_name} ({key}) no existe en PostgreSQL"


def test_seed_catalogs_present():
    """Verifica la presencia de datos semilla críticos."""
    engine = get_engine()
    with engine.connect() as conn:
        # Estados
        estados = conn.execute(text("SELECT nombre FROM estado_activo;")).scalars().all()
        assert set(estados) == {"EN_USO", "EN_MANTENIMIENTO", "DADO_DE_BAJA", "VENDIDO"}

        # Cuentas PCGE
        cuentas = conn.execute(text("SELECT codigo FROM cuenta_contable;")).scalars().all()
        for expected_acc in ["3321", "3361", "3952", "3956", "6814"]:
            assert expected_acc in cuentas, f"Falta cuenta contable {expected_acc}"

        # Categorías
        categorias = conn.execute(text("SELECT nombre, vida_util_meses, tasa_anual FROM categoria_activo;")).fetchall()
        cat_map = {row[0]: (row[1], float(row[2])) for row in categorias}
        assert "Equipos de Cómputo" in cat_map
        assert cat_map["Equipos de Cómputo"] == (48, 25.00)
        assert "Edificaciones" in cat_map
        assert cat_map["Edificaciones"] == (240, 5.00)


def test_check_constraint_activo_fecha_uso():
    """Verifica que fecha_inicio_uso < fecha_adquisicion dispare error CHECK."""
    engine = get_engine()
    with engine.connect() as conn:
        # Obtener IDs necesarios para crear activo
        id_cat = conn.execute(text("SELECT id_categoria FROM categoria_activo LIMIT 1;")).scalar()
        id_est = conn.execute(text("SELECT id_estado FROM estado_activo WHERE nombre='EN_USO';")).scalar()
        id_ub = conn.execute(text("SELECT id_ubicacion FROM ubicacion LIMIT 1;")).scalar()
        id_cc = conn.execute(text("SELECT id_centro_costo FROM centro_costo LIMIT 1;")).scalar()

        # Crear proveedor, empleado y documento si no existen
        conn.execute(
            text(
                """
                INSERT INTO proveedor (tipo_documento, ruc, razon_social)
                VALUES ('6', '20999999991', 'PROV TEST SAC')
                ON CONFLICT (ruc) DO NOTHING;
                """
            )
        )
        id_prov = conn.execute(text("SELECT id_proveedor FROM proveedor WHERE ruc='20999999991';")).scalar()

        conn.execute(
            text(
                """
                INSERT INTO empleado (dni, nombres, apellidos, cargo, id_centro_costo)
                VALUES ('99887766', 'Tester', 'Pruebas', 'Auditor', :id_cc)
                ON CONFLICT (dni) DO NOTHING;
                """
            ),
            {"id_cc": id_cc},
        )
        id_emp = conn.execute(text("SELECT id_empleado FROM empleado WHERE dni='99887766';")).scalar()

        conn.execute(
            text(
                """
                INSERT INTO documento_adquisicion (id_proveedor, tipo_documento, tipo_comprobante, numero, fecha_emision, moneda, monto_total)
                VALUES (:id_prov, 'FACTURA', '01', 'F001-TEST-01', '2026-01-10', 'PEN', 5000.00)
                ON CONFLICT (id_proveedor, tipo_documento, numero) DO NOTHING;
                """
            ),
            {"id_prov": id_prov},
        )
        id_doc = conn.execute(
            text(
                "SELECT id_documento FROM documento_adquisicion WHERE id_proveedor=:id_prov AND numero='F001-TEST-01';"
            ),
            {"id_prov": id_prov},
        ).scalar()
        conn.commit()

        # Intento de inserción con fecha_inicio_uso anterior a fecha_adquisicion
        with pytest.raises(IntegrityError) as exc_info:
            conn.execute(
                text(
                    """
                    INSERT INTO activo_fijo (
                        codigo, descripcion, id_categoria, id_estado, id_ubicacion,
                        id_centro_costo, id_responsable, id_documento,
                        fecha_adquisicion, fecha_inicio_uso, costo_adquisicion, vida_util_meses
                    ) VALUES (
                        'TEST-FAIL-01', 'Activo Invalido', :id_cat, :id_est, :id_ub,
                        :id_cc, :id_emp, :id_doc,
                        '2026-05-10', '2026-05-01', 1000.00, 12
                    );
                    """
                ),
                {
                    "id_cat": id_cat,
                    "id_est": id_est,
                    "id_ub": id_ub,
                    "id_cc": id_cc,
                    "id_emp": id_emp,
                    "id_doc": id_doc,
                },
            )
        assert "ck_activo_fecha_uso" in str(exc_info.value).lower() or "check" in str(exc_info.value).lower()


def test_check_constraint_traslado_mismas_ubicaciones():
    """Verifica que no se pueda registrar un traslado donde origen == destino."""
    engine = get_engine()
    with engine.connect() as conn:
        id_ub = conn.execute(text("SELECT id_ubicacion FROM ubicacion LIMIT 1;")).scalar()
        id_emp = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()
        
        # Obtener un activo válido existente o insertar uno válido
        id_cat = conn.execute(text("SELECT id_categoria FROM categoria_activo LIMIT 1;")).scalar()
        id_est = conn.execute(text("SELECT id_estado FROM estado_activo WHERE nombre='EN_USO';")).scalar()
        id_cc = conn.execute(text("SELECT id_centro_costo FROM centro_costo LIMIT 1;")).scalar()
        id_doc = conn.execute(text("SELECT id_documento FROM documento_adquisicion LIMIT 1;")).scalar()

        conn.execute(
            text(
                """
                INSERT INTO activo_fijo (
                    codigo, descripcion, id_categoria, id_estado, id_ubicacion,
                    id_centro_costo, id_responsable, id_documento,
                    fecha_adquisicion, fecha_inicio_uso, costo_adquisicion, vida_util_meses
                ) VALUES (
                    'TEST-TRASLADO-ACTIVO', 'Activo Traslado', :id_cat, :id_est, :id_ub,
                    :id_cc, :id_emp, :id_doc,
                    '2026-01-01', '2026-01-02', 3000.00, 24
                ) ON CONFLICT (codigo) DO NOTHING;
                """
            ),
            {
                "id_cat": id_cat,
                "id_est": id_est,
                "id_ub": id_ub,
                "id_cc": id_cc,
                "id_emp": id_emp,
                "id_doc": id_doc,
            },
        )
        conn.commit()

        id_act = conn.execute(text("SELECT id_activo FROM activo_fijo WHERE codigo='TEST-TRASLADO-ACTIVO';")).scalar()

        with pytest.raises(IntegrityError) as exc_info:
            conn.execute(
                text(
                    """
                    INSERT INTO traslado_activo (
                        id_activo, id_ubicacion_origen, id_ubicacion_destino, fecha, motivo, id_autorizado_por
                    ) VALUES (
                        :id_act, :id_ub, :id_ub, '2026-03-01', 'Traslado Inválido', :id_emp
                    );
                    """
                ),
                {"id_act": id_act, "id_ub": id_ub, "id_emp": id_emp},
            )
        assert "ck_traslado_ubicacion" in str(exc_info.value).lower() or "check" in str(exc_info.value).lower()


def test_unique_constraint_periodo_contable():
    """Verifica que no se puedan duplicar periodos contables (anio, mes)."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                INSERT INTO periodo_contable (anio, mes, estado)
                VALUES (2026, 1, 'ABIERTO')
                ON CONFLICT (anio, mes) DO NOTHING;
                """
            )
        )
        conn.commit()

        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO periodo_contable (anio, mes, estado)
                    VALUES (2026, 1, 'CERRADO');
                    """
                )
            )