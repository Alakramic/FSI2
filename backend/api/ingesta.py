"""
backend/api/ingesta.py
Endpoints HTTP para Ingesta y Extracción de Comprobantes con IA.
"""

from typing import Optional
from pathlib import Path
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel

from backend.models.pydantic_schemas import FacturaExtraccionResultado
from backend.services.ai_extractor import extract_from_invoice
from backend.services.ingestion_service import persist_ingested_invoice

router = APIRouter(prefix="/ingesta", tags=["Ingesta con IA"])


class ConfirmarIngestaRequest(BaseModel):
    extraccion: FacturaExtraccionResultado
    id_responsable: int
    id_ubicacion: int
    id_centro_costo: Optional[int] = None


@router.post("/extraer")
async def extraer_factura(
    archivo: UploadFile = File(...),
    mock: bool = Form(False),
):
    """Sube un archivo de factura (PDF, imagen o JSON mock) y procesa la extracción inteligente con IA."""
    suffix = Path(archivo.filename or "archivo.bin").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await archivo.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        resultado = extract_from_invoice(tmp_path, mock_mode=mock)
        return resultado
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error en extracción con IA: {str(exc)}")
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.post("/confirmar")
def confirmar_ingesta(req: ConfirmarIngestaRequest):
    """Confirma la incorporación de los activos extraídos y persiste en PostgreSQL."""
    try:
        guardado = persist_ingested_invoice(
            extraction=req.extraccion,
            id_responsable=req.id_responsable,
            id_ubicacion=req.id_ubicacion,
            id_centro_costo=req.id_centro_costo,
        )
        return guardado
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))