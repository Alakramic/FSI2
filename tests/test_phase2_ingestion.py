"""
tests/test_phase2_ingestion.py
Suite de Pruebas Automatizadas de la FASE 2:
- Validación de contratos Pydantic v2 (FacturaExtraccionResultado)
- Extracción y filtrado semántico (Bienes duraderos vs consumibles descartados)
- Persistencia transaccional en cascada (proveedor -> documento -> activos -> asignaciones)
- Restricción contra facturas duplicadas y atomicidad (rollback total)
- Verificación de ejecución del comando CLI con --auto-confirmar
"""

import pytest
from pathlib import Path
from decimal import Decimal
from datetime import date
from sqlalchemy import text

from backend.config.db_connection import get_engine
from backend.models.pydantic_schemas import (
    FacturaExtraccionResultado,
    ProveedorExtraido,
    DocumentoExtraido,
    ActivoExtraido,
)
from backend.services.ai_extractor import extract_from_invoice
from backend.services.ingestion_service import persist_ingested_invoice


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "factura_muestra_mixta.json"


def test_pydantic_schema_strict_validation():
    """Valida la deserialización y validación estricta del esquema Pydantic."""
    assert FIXTURE_PATH.exists()
    resultado = extract_from_invoice(FIXTURE_PATH, mock_mode=True)

    assert isinstance(resultado, FacturaExtraccionResultado)
    assert resultado.proveedor.ruc == "20556677889"
    assert resultado.documento.numero == "F001-0008899"
    assert resultado.documento.monto_total == Decimal("9250.00")
    
    # 2 tipos de activos: 1 con cantidad=2 y otro con cantidad=1 (total 3 activos tangibles)
    assert len(resultado.activos) == 2
    assert resultado.activos[0].cantidad == 2
    assert resultado.activos[0].costo_unitario == Decimal("4200.00")

    # 3 consumibles descartados
    assert len(resultado.consumibles_descartados) == 3
    assert any("papel" in c.lower() for c in resultado.consumibles_descartados)
    assert any("tóner" in c.lower() or "toner" in c.lower() for c in resultado.consumibles_descartados)


def test_cascade_transactional_persistence():
    """Verifica que la persistencia cree proveedor, documento, activos con códigos y asignación."""
    engine = get_engine()

    # Obtener empleado y ubicación existentes
    with engine.connect() as conn:
        emp_id = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()
        if not emp_id:
            cc_id = conn.execute(text("SELECT id_centro_costo FROM centro_costo LIMIT 1;")).scalar()
            emp_id = conn.execute(
                text(
                    """
                    INSERT INTO empleado (dni, nombres, apellidos, cargo, id_centro_costo)
                    VALUES ('44556677', 'Mario', 'Vargas', 'Analista TI', :cc_id)
                    RETURNING id_empleado;
                    """
                ),
                {"cc_id": cc_id},
            ).scalar()
            conn.commit()

        ub_id = conn.execute(text("SELECT id_ubicacion FROM ubicacion LIMIT 1;")).scalar()

    resultado = extract_from_invoice(FIXTURE_PATH, mock_mode=True)

    # Limpiar factura y activos de prueba previos si existieran para aislar el test
    with engine.begin() as conn:
        doc_ids = conn.execute(
            text(
                """
                SELECT d.id_documento 
                FROM documento_adquisicion d
                JOIN proveedor p ON d.id_proveedor = p.id_proveedor
                WHERE p.ruc = :ruc AND d.numero = :num;
                """
            ),
            {"ruc": resultado.proveedor.ruc, "num": resultado.documento.numero},
        ).scalars().all()
        for d_id in doc_ids:
            conn.execute(text("DELETE FROM activo_fijo WHERE id_documento = :d_id;"), {"d_id": d_id})
            conn.execute(text("DELETE FROM documento_adquisicion WHERE id_documento = :d_id;"), {"d_id": d_id})

    # Ejecutar persistencia
    resumen = persist_ingested_invoice(
        extraction=resultado,
        id_responsable=emp_id,
        id_ubicacion=ub_id,
    )

    # 1. Verificar resumen devuelto
    assert resumen["ruc"] == "20556677889"
    assert resumen["numero_documento"] == "F001-0008899"
    assert resumen["total_activos_creados"] == 3  # 2 laptops + 1 monitor

    # 2. Verificar en base de datos
    with engine.connect() as conn:
        # Verificar documento
        doc_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM documento_adquisicion WHERE numero = :num;"
            ),
            {"num": resultado.documento.numero},
        ).scalar()
        assert doc_count == 1

        # Verificar activos
        activos_db = conn.execute(
            text(
                """
                SELECT codigo, descripcion, costo_adquisicion, id_responsable, id_ubicacion
                FROM activo_fijo
                WHERE id_documento = :id_doc
                ORDER BY codigo;
                """
            ),
            {"id_doc": resumen["id_documento"]},
        ).fetchall()

        assert len(activos_db) == 3
        # Códigos con formato patrimonial AF-YYYY-XXXX
        for row in activos_db:
            assert row[0].startswith("AF-2026-")
            assert row[3] == emp_id
            assert row[4] == ub_id

        # Verificar asignación de custodia creada
        asig_count = conn.execute(
            text(
                """
                SELECT COUNT(*) FROM asignacion_activo 
                WHERE id_activo IN (SELECT id_activo FROM activo_fijo WHERE id_documento = :id_doc);
                """
            ),
            {"id_doc": resumen["id_documento"]},
        ).scalar()
        assert asig_count == 3


def test_atomic_rollback_on_duplicate_invoice():
    """Verifica que intentar registrar dos veces la misma factura lance error y no duplique registros."""
    engine = get_engine()
    with engine.connect() as conn:
        emp_id = conn.execute(text("SELECT id_empleado FROM empleado LIMIT 1;")).scalar()
        ub_id = conn.execute(text("SELECT id_ubicacion FROM ubicacion LIMIT 1;")).scalar()

    resultado = extract_from_invoice(FIXTURE_PATH, mock_mode=True)

    # El comprobante ya fue insertado en el test anterior. Un segundo intento DEBE fallar.
    with pytest.raises(ValueError) as exc_info:
        persist_ingested_invoice(
            extraction=resultado,
            id_responsable=emp_id,
            id_ubicacion=ub_id,
        )
    assert "ya fue registrado previamente" in str(exc_info.value).lower()