"""
backend/database/seed.py
Semillero de datos iniciales para el SGAF:
- Estados de activo
- Cuentas contables PCGE (Cuentas 33, 39, 68)
- Categorías base de activos fijos con vida útil y tasas SUNAT
- Centros de costo y ubicaciones base
"""

from typing import Dict, Any, List
from sqlalchemy import text
from backend.config.db_connection import get_engine
from backend.config.db_schema import TABLES, COLUMNS, t, col


def seed_database() -> Dict[str, int]:
    """Inserta datos semilla en la base de datos de manera idempotente."""
    engine = get_engine()
    results = {
        "estados": 0,
        "cuentas": 0,
        "categorias": 0,
        "centros_costo": 0,
        "ubicaciones": 0,
    }

    with engine.begin() as conn:
        # 1. Estados de activo
        estados = ["EN_USO", "EN_MANTENIMIENTO", "DADO_DE_BAJA", "VENDIDO"]
        tabla_estado = t("ESTADO_ACTIVO")
        col_nombre = col("ESTADO_ACTIVO", "NOMBRE")
        for estado in estados:
            sql = text(
                f"""
                INSERT INTO {tabla_estado} ({col_nombre})
                VALUES (:nombre)
                ON CONFLICT ({col_nombre}) DO NOTHING;
                """
            )
            res = conn.execute(sql, {"nombre": estado})
            results["estados"] += res.rowcount

        # 2. Cuentas Contables PCGE
        cuentas = [
            # Activos (Elemento 33)
            ("3321", "Edificaciones - Costo de adquisición o construcción"),
            ("3331", "Maquinarias y equipos de explotación"),
            ("3341", "Vehículos motorizados - Equipo de transporte"),
            ("3351", "Muebles y enseres"),
            ("3361", "Equipos para procesamiento de información (Cómputo)"),
            # Depreciación acumulada (Elemento 39)
            ("3952", "Depreciación acumulada - Edificaciones"),
            ("3953", "Depreciación acumulada - Maquinarias y equipos"),
            ("3954", "Depreciación acumulada - Equipos de transporte"),
            ("3955", "Depreciación acumulada - Muebles y enseres"),
            ("3956", "Depreciación acumulada - Equipos de cómputo"),
            # Gastos de depreciación (Elemento 68)
            ("6814", "Depreciación de propiedad, planta y equipo - Costo"),
        ]
        tabla_cuenta = t("CUENTA_CONTABLE")
        col_cta_cod = col("CUENTA_CONTABLE", "CODIGO")
        col_cta_nom = col("CUENTA_CONTABLE", "NOMBRE")
        for codigo, nombre in cuentas:
            sql = text(
                f"""
                INSERT INTO {tabla_cuenta} ({col_cta_cod}, {col_cta_nom})
                VALUES (:codigo, :nombre)
                ON CONFLICT ({col_cta_cod}) DO NOTHING;
                """
            )
            res = conn.execute(sql, {"codigo": codigo, "nombre": nombre})
            results["cuentas"] += res.rowcount

        # 3. Categorías de Activo Fijo
        # Helper para obtener id_cuenta por código
        def get_cuenta_id(codigo: str) -> int:
            row = conn.execute(
                text(f"SELECT id_cuenta FROM {tabla_cuenta} WHERE {col_cta_cod} = :codigo"),
                {"codigo": codigo},
            ).fetchone()
            if not row:
                raise ValueError(f"Cuenta contable no encontrada: {codigo}")
            return row[0]

        id_gasto_6814 = get_cuenta_id("6814")

        categorias = [
            {
                "nombre": "Edificaciones",
                "vida_util_meses": 240,  # 20 años
                "tasa_anual": 5.00,
                "id_cuenta_activo": get_cuenta_id("3321"),
                "id_cuenta_dep_acum": get_cuenta_id("3952"),
                "id_cuenta_gasto": id_gasto_6814,
            },
            {
                "nombre": "Maquinaria y Equipo",
                "vida_util_meses": 120,  # 10 años
                "tasa_anual": 10.00,
                "id_cuenta_activo": get_cuenta_id("3331"),
                "id_cuenta_dep_acum": get_cuenta_id("3953"),
                "id_cuenta_gasto": id_gasto_6814,
            },
            {
                "nombre": "Equipos de Transporte",
                "vida_util_meses": 60,  # 5 años
                "tasa_anual": 20.00,
                "id_cuenta_activo": get_cuenta_id("3341"),
                "id_cuenta_dep_acum": get_cuenta_id("3954"),
                "id_cuenta_gasto": id_gasto_6814,
            },
            {
                "nombre": "Muebles y Enseres",
                "vida_util_meses": 120,  # 10 años
                "tasa_anual": 10.00,
                "id_cuenta_activo": get_cuenta_id("3351"),
                "id_cuenta_dep_acum": get_cuenta_id("3955"),
                "id_cuenta_gasto": id_gasto_6814,
            },
            {
                "nombre": "Equipos de Cómputo",
                "vida_util_meses": 48,  # 4 años
                "tasa_anual": 25.00,
                "id_cuenta_activo": get_cuenta_id("3361"),
                "id_cuenta_dep_acum": get_cuenta_id("3956"),
                "id_cuenta_gasto": id_gasto_6814,
            },
        ]

        tabla_cat = t("CATEGORIA_ACTIVO")
        for cat in categorias:
            sql = text(
                f"""
                INSERT INTO {tabla_cat} (
                    nombre, vida_util_meses, metodo_depreciacion, tasa_anual,
                    id_cuenta_activo, id_cuenta_dep_acum, id_cuenta_gasto
                )
                VALUES (
                    :nombre, :vida_util_meses, 'LINEA_RECTA', :tasa_anual,
                    :id_cuenta_activo, :id_cuenta_dep_acum, :id_cuenta_gasto
                )
                ON CONFLICT (nombre) DO NOTHING;
                """
            )
            res = conn.execute(sql, cat)
            results["categorias"] += res.rowcount

        # 4. Centros de Costo Base
        centros = [
            ("CC-001", "Dirección y Administración"),
            ("CC-002", "Operaciones y Logística"),
            ("CC-003", "Tecnología de la Información"),
        ]
        tabla_cc = t("CENTRO_COSTO")
        col_cc_cod = col("CENTRO_COSTO", "CODIGO")
        col_cc_nom = col("CENTRO_COSTO", "NOMBRE")
        for codigo, nombre in centros:
            sql = text(
                f"""
                INSERT INTO {tabla_cc} ({col_cc_cod}, {col_cc_nom})
                VALUES (:codigo, :nombre)
                ON CONFLICT ({col_cc_cod}) DO NOTHING;
                """
            )
            res = conn.execute(sql, {"codigo": codigo, "nombre": nombre})
            results["centros_costo"] += res.rowcount

        # 5. Ubicaciones Base
        ubicaciones = [
            ("Sede Principal - Administración", "Sede Central Lima", None),
            ("Sede Principal - Data Center", "Sede Central Lima", None),
            ("Almacén General de Activos", "Sede Callao", None),
        ]
        tabla_ub = t("UBICACION")
        col_ub_nom = col("UBICACION", "NOMBRE")
        col_ub_sede = col("UBICACION", "SEDE")
        for nom, sede, padre in ubicaciones:
            sql_check = text(
                f"SELECT 1 FROM {tabla_ub} WHERE {col_ub_nom} = :nom AND {col_ub_sede} = :sede"
            )
            exists = conn.execute(sql_check, {"nom": nom, "sede": sede}).scalar()
            if not exists:
                conn.execute(
                    text(
                        f"INSERT INTO {tabla_ub} ({col_ub_nom}, {col_ub_sede}) VALUES (:nom, :sede)"
                    ),
                    {"nom": nom, "sede": sede},
                )
                results["ubicaciones"] += 1

    return results


if __name__ == "__main__":
    seeded = seed_database()
    print("Semillero completado exitosamente:", seeded)