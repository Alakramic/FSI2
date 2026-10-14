"""
tests/conftest.py
Configuración global de fixtures para pytest.
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from sqlalchemy import text
from backend.config.db_connection import get_engine, get_session_factory
from backend.database.migrator import run_migrations
from backend.database.seed import seed_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Asegura que el esquema esté migrado y sembrado antes de ejecutar pruebas."""
    run_migrations()
    seed_database()
    yield