"""
backend/services/ingestion_service.py
Servicio de Persistencia Transaccional Atómica para Ingesta de Comprobantes.
Garantiza inserción en cascada en proveedor, documento_adquisicion,
generación secuencial de activo_fijo y asignación inicial a custodio.
"""

from typing import Dict, Any, List, Optional
from datetime import date
from decimal import Decimal
from sqlalchemy import text
from backend.config.db_connection import get_engine
from backend.config.db_schema import t, col
from backend.models.pydantic_schemas import FacturaExtraccionResultado, ActivoExtraido

# Mapeo de Categoría de Activo a Código PLE Tabla 18 SUNAT
PLE_TIPO_ACTIVO_MAP = {
    "edificaciones": "01",
    "maquinaria y equipo": "02",
    "equipos de transporte": "03",
    "equipos de cómputo": "04",
    "muebles y enseres": "05",
}


def _get_next_asset_code(conn, prefix: str = "AF", year: Optional[int] = None) -> str:
    """Genera el siguiente código patrimonial secuencial (ej: AF-2026-0001)."""
    current_year = year or date.today().year
    pattern = f"{prefix}-{current_year}-%"

    row = conn.execute(
        text(
            """
            SELECT codigo 
            FROM activo_fijo 
            WHERE codigo LIKE :pattern 
            ORDER BY codigo DESC 
            LIMIT 1;
            """
        ),
        {"pattern": pattern},
    ).fetchone()

    if not row or not row[0]:
        return f"{prefix}-{current_year}-0001"

    last_code = row[0]
    parts = last_code.split("-")
    if len(parts) >= 3 and parts[-1].isdigit():
        next_seq = int(parts[-1]) + 1
        return f"{prefix}-{current_year}-{next_seq:04d}"
    return f"{prefix}-{current_year}-0001"


def persist_ingested_invoice(
    extraction: FacturaExtraccionResultado,
    id_responsable: int,
    id_ubicacion: int,
    id_centro_costo: Optional[int] = None,
    codigo_prefix: str = "AF",
) -> Dict[str, Any]:
    """
    Ejecuta la persistencia atómica en cascada de la factura y sus activos fijos.
    Si cualquier paso falla, se produce un rollback completo de la transacción.
    """
    engine = get_engine()

    with engine.begin() as conn:
        # 1. Validar existencia del responsable y obtener su centro de costo si no se especificó
        emp_row = conn.execute(
            text(
                """
                SELECT id_empleado, id_centro_costo, nombres || ' ' || apellidos AS nombre_completo 
                FROM empleado 
                WHERE id_empleado = :id_emp;
                """
            ),
            {"id_emp": id_responsable},
        ).fetchone()

        if not emp_row:
            raise ValueError(f"No existe el empleado custodio con ID: {id_responsable}")

        resolved_centro_costo = id_centro_costo or emp_row[1]

        # Validar existencia de la ubicación
        ub_exists = conn.execute(
            text("SELECT 1 FROM ubicacion WHERE id_ubicacion = :id_ub;"),
            {"id_ub": id_ubicacion},
        ).scalar()
        if not ub_exists:
            raise ValueError(f"No existe la ubicación con ID: {id_ubicacion}")

        # Obtener id del estado 'EN_USO'
        id_estado_en_uso = conn.execute(
            text("SELECT id_estado FROM estado_activo WHERE nombre = 'EN_USO';")
        ).scalar()
        if not id_estado_en_uso:
            raise ValueError("No se encontró el estado 'EN_USO' en el catálogo estado_activo")

        # 2. Registrar o recuperar Proveedor
        prov = extraction.proveedor
        prov_row = conn.execute(
            text("SELECT id_proveedor FROM proveedor WHERE ruc = :ruc;"),
            {"ruc": prov.ruc},
        ).fetchone()

        if prov_row:
            id_proveedor = prov_row[0]
        else:
            id_proveedor = conn.execute(
                text(
                    """
                    INSERT INTO proveedor (tipo_documento, ruc, razon_social, telefono, email)
                    VALUES (:tipo_doc, :ruc, :razon_social, :telefono, :email)
                    RETURNING id_proveedor;
                    """
                ),
                {
                    "tipo_doc": prov.tipo_documento,
                    "ruc": prov.ruc,
                    "razon_social": prov.razon_social,
                    "telefono": prov.telefono,
                    "email": prov.email,
                },
            ).scalar()

        # 3. Registrar Documento de Adquisición (verificar duplicado)
        doc = extraction.documento
        doc_exists = conn.execute(
            text(
                """
                SELECT id_documento 
                FROM documento_adquisicion 
                WHERE id_proveedor = :id_prov 
                  AND tipo_documento = :tipo_doc 
                  AND numero = :numero;
                """
            ),
            {
                "id_prov": id_proveedor,
                "tipo_doc": doc.tipo_documento,
                "numero": doc.numero,
            },
        ).scalar()

        if doc_exists:
            raise ValueError(
                f"El comprobante {doc.tipo_documento} {doc.numero} del proveedor {prov.ruc} "
                "ya fue registrado previamente en el sistema."
            )

        id_documento = conn.execute(
            text(
                """
                INSERT INTO documento_adquisicion (
                    id_proveedor, tipo_documento, tipo_comprobante, numero,
                    fecha_emision, moneda, monto_total
                ) VALUES (
                    :id_prov, :tipo_doc, :tipo_comp, :numero,
                    :fecha_emision, :moneda, :monto_total
                ) RETURNING id_documento;
                """
            ),
            {
                "id_prov": id_proveedor,
                "tipo_doc": doc.tipo_documento,
                "tipo_comp": doc.tipo_comprobante,
                "numero": doc.numero,
                "fecha_emision": doc.fecha_emision,
                "moneda": doc.moneda,
                "monto_total": doc.monto_total,
            },
        ).scalar()

        # 4. Procesar y registrar cada Activo Fijo
        # Cargar catálogo de categorías para resolución
        cat_rows = conn.execute(
            text("SELECT id_categoria, nombre, vida_util_meses FROM categoria_activo;")
        ).fetchall()
        cat_lookup = {row[1].lower(): (row[0], row[2]) for row in cat_rows}

        # Fallback a "equipos de cómputo" o la primera categoría si no coincide
        default_cat_id, default_vida_util = next(iter(cat_lookup.values()))
        if "equipos de cómputo" in cat_lookup:
            default_cat_id, default_vida_util = cat_lookup["equipos de cómputo"]

        activos_creados: List[Dict[str, Any]] = []

        doc_year = doc.fecha_emision.year

        for item in extraction.activos:
            # Resolver categoría
            cat_key = item.categoria_sugerida.lower().strip()
            cat_id, vida_util = cat_lookup.get(cat_key, (default_cat_id, default_vida_util))
            ple_tipo_activo = PLE_TIPO_ACTIVO_MAP.get(cat_key, "04")

            # Crear una fila por cada unidad adquirida
            for u in range(item.cantidad):
                codigo_generado = _get_next_asset_code(conn, prefix=codigo_prefix, year=doc_year)
                
                # Manejar número de serie si hay múltiples unidades
                serie_unit = item.numero_serie
                if item.cantidad > 1 and item.numero_serie:
                    serie_unit = f"{item.numero_serie}-{u+1}"

                id_activo = conn.execute(
                    text(
                        """
                        INSERT INTO activo_fijo (
                            codigo, catalogo_tipo_id, tipo_activo_ple, estado_activo_ple,
                            descripcion, marca, modelo, numero_serie,
                            id_categoria, id_estado, id_ubicacion, id_centro_costo,
                            id_responsable, id_documento, fecha_adquisicion,
                            fecha_inicio_uso, costo_adquisicion, valor_residual,
                            vida_util_meses, metodo_depreciacion
                        ) VALUES (
                            :codigo, '9', :tipo_ple, '1',
                            :descripcion, :marca, :modelo, :serie,
                            :id_categoria, :id_estado, :id_ubicacion, :id_centro_costo,
                            :id_responsable, :id_documento, :fecha_adq,
                            :fecha_uso, :costo, 0.00,
                            :vida_util, '1'
                        ) RETURNING id_activo;
                        """
                    ),
                    {
                        "codigo": codigo_generado,
                        "tipo_ple": ple_tipo_activo,
                        "descripcion": item.descripcion,
                        "marca": item.marca,
                        "modelo": item.modelo,
                        "serie": serie_unit,
                        "id_categoria": cat_id,
                        "id_estado": id_estado_en_uso,
                        "id_ubicacion": id_ubicacion,
                        "id_centro_costo": resolved_centro_costo,
                        "id_responsable": id_responsable,
                        "id_documento": id_documento,
                        "fecha_adq": doc.fecha_emision,
                        "fecha_uso": doc.fecha_emision,
                        "costo": item.costo_unitario,
                        "vida_util": vida_util,
                    },
                ).scalar()

                # 5. Registrar Asignación Inicial de Custodia
                conn.execute(
                    text(
                        """
                        INSERT INTO asignacion_activo (
                            id_activo, id_empleado, fecha_inicio, observacion
                        ) VALUES (
                            :id_act, :id_emp, :fecha_ini, :obs
                        );
                        """
                    ),
                    {
                        "id_act": id_activo,
                        "id_emp": id_responsable,
                        "fecha_ini": doc.fecha_emision,
                        "obs": f"Custodia inicial asignada por adquisición en comprobante {doc.numero}",
                    },
                )

                activos_creados.append(
                    {
                        "id_activo": id_activo,
                        "codigo": codigo_generado,
                        "descripcion": item.descripcion,
                        "marca": item.marca,
                        "modelo": item.modelo,
                        "numero_serie": serie_unit,
                        "costo": float(item.costo_unitario),
                        "categoria_id": cat_id,
                        "vida_util_meses": vida_util,
                    }
                )

    return {
        "id_proveedor": id_proveedor,
        "razon_social": prov.razon_social,
        "ruc": prov.ruc,
        "id_documento": id_documento,
        "numero_documento": doc.numero,
        "tipo_documento": doc.tipo_documento,
        "fecha_emision": str(doc.fecha_emision),
        "total_activos_creados": len(activos_creados),
        "activos": activos_creados,
        "consumibles_descartados": extraction.consumibles_descartados,
    }