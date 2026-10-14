"""
backend/api/depreciacion_endpoints.py
Endpoints HTTP para Cierre Mensual de Depreciación.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.services.depreciation_service import calculate_and_close_monthly_depreciation

router = APIRouter(prefix="/depreciacion", tags=["Depreciación"])


class CierrePeriodoRequest(BaseModel):
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    forzar: bool = False


@router.post("/cerrar-mes")
def api_cerrar_mes(req: CierrePeriodoRequest):
    """Ejecuta el devengo de depreciación y bloquea el periodo contable en PostgreSQL."""
    try:
        resumen = calculate_and_close_monthly_depreciation(
            anio=req.anio,
            mes=req.mes,
            force_recalculate=req.forzar,
        )
        return resumen
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))