"""
backend/api/reportes.py
Endpoints de Generación y Descarga de Reportes y Libros Electrónicos Oficiales:
- Libro Electrónico de Activos Fijos SUNAT PLE 7.1 (.txt)
"""

from fastapi import APIRouter, Query, Response
from backend.services.sunat_ple_service import generate_ple_7_1_content

router = APIRouter(prefix="/reportes", tags=["Reportes y SUNAT"])


@router.get("/ple-7-1")
def exportar_ple_7_1(
    anio: int = Query(..., description="Año gravable/ejercicio a exportar (ej: 2026)")
):
    """
    Genera y descarga el archivo plano oficial del Libro de Activos Fijos PLE 7.1
    con formato delimitado por plecas (|) según normativa de SUNAT.
    """
    filename, content_txt, total_reg = generate_ple_7_1_content(anio)

    return Response(
        content=content_txt,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Total-Registros": str(total_reg),
        },
    )