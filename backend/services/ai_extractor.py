"""
backend/services/ai_extractor.py
Pipeline de Extracción Inteligente de Comprobantes con IA (Gemini API - google-genai).
Aplica discriminación semántica estricta para extraer bienes de Activo Fijo (NIC 16)
y descartar suministros y consumibles variables.
"""

import os
import json
import mimetypes
from pathlib import Path
from typing import Optional, Union
from google import genai
from google.genai import types

from backend.models.pydantic_schemas import (
    FacturaExtraccionResultado,
    ProveedorExtraido,
    DocumentoExtraido,
    ActivoExtraido,
)

SYSTEM_PROMPT = """
Eres un Auditor y Contador Senior de Activos Fijos con especialidad en el Plan Contable General Empresarial (PCGE),
la Norma Internacional de Contabilidad 16 (NIC 16 - Propiedades, Planta y Equipo) y la normativa tributaria peruana (SUNAT).

Tu misión es analizar la imagen o documento del comprobante de pago (Factura, Boleta, etc.) y estructurar la información
según el esquema JSON estricto requerido.

REGLAS CRÍTICAS DE CLASIFICACIÓN Y FILTRADO:
1. SOLO EXTRAER ACTIVOS FIJOS (Bienes Duraderos):
   - Bienes corporales/físicos tangibles con vida útil estimada superior a un año.
   - Destinados a ser utilizados en las operaciones, administración o producción de la empresa.
   - Ejemplos: Laptops, Computadoras de escritorio, Monitores, Servidores, Switches, Impresoras o Fotocopiadoras industriales,
     Mobiliario de oficina (escritorios ergonómicos, sillas de oficina, archivadores metálicos), Vehículos,
     Maquinarias y Equipos industriales, Aire acondicionado, etc.
   - Asigna siempre la 'categoria_sugerida' más precisa:
     - 'Equipos de Cómputo'
     - 'Maquinaria y Equipo'
     - 'Equipos de Transporte'
     - 'Muebles y Enseres'
     - 'Edificaciones'

2. DESCARTAR ESTRICTAMENTE CONSUMIBLES, GASTOS Y SUMINISTROS:
   - Todo ítem de rápida rotación, desgaste inmediato o gasto corriente DEBE SER IGNORADO para activo fijo.
   - Ejemplos de ítems descartados: Paquetes de papel bond, tóner, cartuchos de tinta, grapas, clips, lapiceros,
     café, azúcar, implementos de limpieza, cables de red sueltos, accesorios menores, servicios de flete,
     gastos de instalación o licencias de software mensual.
   - Agrega el nombre o descripción de cada ítem descartado a la lista 'consumibles_descartados'.

3. DATOS DE PROVEEDOR Y DOCUMENTO:
   - Extrae el RUC (11 dígitos para empresas en Perú) o documento de identidad, y la Razón Social exacta.
   - Identifica la Serie y Número del comprobante (ej: F001-0004523).
   - Extrae la fecha de emisión (formato YYYY-MM-DD), la moneda (PEN o USD) y el importe total facturado.
"""


def _detect_mime_type(file_path: Path) -> str:
    """Detecta el tipo MIME del archivo comprobante."""
    suffix = file_path.suffix.lower()
    if suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".json":
        return "application/json"
    mime, _ = mimetypes.guess_type(str(file_path))
    return mime or "application/octet-stream"


def extract_from_invoice(
    file_path: Union[str, Path],
    api_key: Optional[str] = None,
    mock_mode: bool = False,
) -> FacturaExtraccionResultado:
    """
    Procesa un comprobante (imagen, PDF o archivo mock) y extrae sus datos
    y bienes clasificados como activo fijo.
    """
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"El archivo del comprobante no existe: {path}")

    # Si es un archivo JSON local o se fuerza mock_mode, procesar directamente
    mime_type = _detect_mime_type(path)
    if mime_type == "application/json" or mock_mode:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        return FacturaExtraccionResultado.model_validate(data)

    gemini_key = api_key or os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError(
            "GEMINI_API_KEY no configurada en las variables de entorno o archivo .env. "
            "Configure GEMINI_API_KEY para utilizar la extracción en vivo de comprobantes."
        )

    client = genai.Client(api_key=gemini_key)
    file_bytes = path.read_bytes()

    # Enviar el archivo junto con el prompt y esquema estructurado
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            SYSTEM_PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FacturaExtraccionResultado,
            temperature=0.1,
        ),
    )

    if not response.text:
        raise RuntimeError("La IA de Gemini no devolvió respuesta para el comprobante.")

    return FacturaExtraccionResultado.model_validate_json(response.text)