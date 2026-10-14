"""
backend/api/catalogos.py
Endpoints de Catálogos Maestros para Selects y Formularios del Frontend.
"""

from fastapi import APIRouter
from sqlalchemy import text
from backend.config.db_connection import get_engine

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


@router.get("/maestros")
def get_catalogos_maestros():
    """Retorna listas de categorías, sedes/ubicaciones, empleados y centros de costo."""
    engine = get_engine()
    with engine.connect() as conn:
        categorias = conn.execute(
            text("SELECT id_categoria, nombre, vida_util_meses, tasa_anual FROM categoria_activo ORDER BY id_categoria;")
        ).fetchall()

        ubicaciones = conn.execute(
            text("SELECT id_ubicacion, nombre, sede FROM ubicacion ORDER BY id_ubicacion;")
        ).fetchall()

        empleados = conn.execute(
            text("SELECT id_empleado, dni, nombres || ' ' || apellidos AS nombre, cargo FROM empleado ORDER BY id_empleado;")
        ).fetchall()

        centros_costo = conn.execute(
            text("SELECT id_centro_costo, codigo, nombre FROM centro_costo ORDER BY id_centro_costo;")
        ).fetchall()

    return {
        "categorias": [
            {"id": r[0], "nombre": r[1], "vida_util_meses": r[2], "tasa_anual": float(r[3])}
            for r in categorias
        ],
        "ubicaciones": [
            {"id": r[0], "nombre": r[1], "sede": r[2]}
            for r in ubicaciones
        ],
        "empleados": [
            {"id": r[0], "dni": r[1], "nombre": r[2], "cargo": r[3]}
            for r in empleados
        ],
        "centros_costo": [
            {"id": r[0], "codigo": r[1], "nombre": r[2]}
            for r in centros_costo
        ],
    }