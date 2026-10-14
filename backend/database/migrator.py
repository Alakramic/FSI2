"""
backend/database/migrator.py
Módulo de migración y ejecución del esquema DDL en PostgreSQL.
"""

from pathlib import Path
from backend.config.db_connection import get_engine

DDL_FILE_PATH = Path(__file__).resolve().parent / "ddl.sql"


def run_migrations(ddl_path: Path = DDL_FILE_PATH) -> bool:
    """Ejecuta el script DDL sobre la base de datos conectada."""
    if not ddl_path.exists():
        raise FileNotFoundError(f"Archivo DDL no encontrado en {ddl_path}")

    # utf-8-sig elimina automáticamente cualquier BOM presente
    sql_content = ddl_path.read_text(encoding="utf-8-sig")
    engine = get_engine()

    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cursor:
            cursor.execute(sql_content)
        raw_conn.commit()
    finally:
        raw_conn.close()

    return True


if __name__ == "__main__":
    run_migrations()
    print("Migración DDL aplicada exitosamente.")