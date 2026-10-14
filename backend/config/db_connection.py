"""
backend/config/db_connection.py
Gestión dinámica y multi-perfil de conexiones a PostgreSQL con SQLAlchemy.
Permite alternar perfiles (local, supabase, dev_team) mediante variables de entorno.
"""

import os
import re
import time
from pathlib import Path
from typing import Generator, Optional, Dict, Any
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# Localizar la raíz del proyecto para cargar .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH, override=True)
else:
    load_dotenv(override=True)

Base = declarative_base()

_current_engine: Optional[Engine] = None
_current_session_factory: Optional[sessionmaker] = None
_current_profile: Optional[str] = None


def mask_database_url(url: str) -> str:
    """Enmascara contraseñas en URLs de base de datos para logs seguros."""
    if not url:
        return ""
    return re.sub(r":([^:@]+)@", ":****@", url)


def get_active_profile() -> str:
    """Retorna el perfil de base de datos actualmente activo."""
    global _current_profile
    if _current_profile:
        return _current_profile
    return os.getenv("DB_PROFILE", "local").strip().lower()


def get_database_url(profile: Optional[str] = None) -> str:
    """
    Obtiene la URL de conexión según el perfil solicitado o activo.
    Prioriza DATABASE_URL_<PERFIL> y cae en fallback según el perfil.
    """
    target_profile = (profile or get_active_profile()).strip().lower()
    env_var_name = f"DATABASE_URL_{target_profile.upper()}"
    url = os.getenv(env_var_name)

    if not url and target_profile == "local":
        url = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/activos_fijos_db"

    if not url:
        raise ValueError(
            f"No se encontró URL configurada para el perfil '{target_profile}'. "
            f"Defina {env_var_name} en el archivo .env"
        )
    return url


def get_engine(profile: Optional[str] = None) -> Engine:
    """Retorna el motor SQLAlchemy correspondiente al perfil activo o solicitado."""
    global _current_engine, _current_profile
    target_profile = (profile or get_active_profile()).strip().lower()

    if _current_engine is not None and _current_profile == target_profile:
        return _current_engine

    db_url = get_database_url(target_profile)
    # Soporte para pool_pre_ping para reconexiones automáticas
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        future=True,
    )

    if profile is None or target_profile == get_active_profile():
        _current_engine = engine
        _current_profile = target_profile

    return engine


def get_session_factory(profile: Optional[str] = None) -> sessionmaker:
    """Retorna la fábrica de sesiones para el perfil actual."""
    global _current_session_factory
    engine = get_engine(profile)
    if _current_session_factory is None or profile is not None:
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _current_session_factory


def get_db() -> Generator[Session, None, None]:
    """Generador de sesión SQLAlchemy para inyección de dependencias en FastAPI."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
    finally:
        session.close()


def switch_profile(new_profile: str) -> bool:
    """
    Cambia dinámicamente el perfil activo en memoria y en el archivo .env.
    """
    global _current_engine, _current_session_factory, _current_profile
    new_profile = new_profile.strip().lower()

    # Validar que exista URL para el nuevo perfil
    try:
        _ = get_database_url(new_profile)
    except ValueError as err:
        raise err

    _current_profile = new_profile
    if _current_engine is not None:
        _current_engine.dispose()
    _current_engine = None
    _current_session_factory = None

    # Actualizar archivo .env si existe
    if ENV_PATH.exists():
        content = ENV_PATH.read_text(encoding="utf-8")
        if re.search(r"^DB_PROFILE=.*$", content, flags=re.MULTILINE):
            content = re.sub(
                r"^DB_PROFILE=.*$",
                f"DB_PROFILE={new_profile}",
                content,
                flags=re.MULTILINE,
            )
        else:
            content += f"\nDB_PROFILE={new_profile}\n"
        ENV_PATH.write_text(content, encoding="utf-8")

    os.environ["DB_PROFILE"] = new_profile
    # Reiniciar engine
    get_engine(new_profile)
    return True


def ping_db(profile: Optional[str] = None) -> Dict[str, Any]:
    """
    Ejecuta un diagnóstico de latencia y versión sobre la base de datos configurada.
    """
    target_profile = (profile or get_active_profile()).strip().lower()
    start_time = time.perf_counter()
    try:
        engine = get_engine(target_profile)
        raw_url = str(engine.url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();")).scalar()
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "ok",
            "profile": target_profile,
            "database_url": mask_database_url(raw_url),
            "version": result,
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        try:
            raw_url = get_database_url(target_profile)
        except Exception:
            raw_url = ""
        return {
            "status": "error",
            "profile": target_profile,
            "database_url": mask_database_url(raw_url),
            "version": None,
            "latency_ms": latency_ms,
            "error": str(exc),
        }