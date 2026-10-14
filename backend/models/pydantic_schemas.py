"""
backend/models/pydantic_schemas.py
Esquemas Pydantic v2 para validación, estructuración de salida de IA (Structured Outputs)
y contratos de datos de la API / CLI.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class ProveedorExtraido(BaseModel):
    """Datos de la empresa proveedora emisora del comprobante."""
    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_documento: str = Field(
        default="6",
        description="Tipo de documento según Tabla 2 SUNAT: '6' para RUC, '1' para DNI"
    )
    ruc: str = Field(
        ...,
        description="Número de RUC (11 dígitos) o DNI del proveedor"
    )
    razon_social: str = Field(
        ...,
        description="Razón social o nombre comercial completo del proveedor"
    )
    telefono: Optional[str] = Field(None, description="Teléfono de contacto si figura en la factura")
    email: Optional[str] = Field(None, description="Correo electrónico si figura en la factura")


class DocumentoExtraido(BaseModel):
    """Datos del comprobante de pago emitido."""
    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_documento: str = Field(
        default="FACTURA",
        description="Tipo de documento: FACTURA, BOLETA, GUIA, ORDEN_COMPRA"
    )
    tipo_comprobante: str = Field(
        default="01",
        description="Código según Tabla 10 SUNAT: '01' Factura, '03' Boleta, '50' DUA"
    )
    numero: str = Field(
        ...,
        description="Serie y número del comprobante (ej: F001-0004523, E001-124)"
    )
    fecha_emision: date = Field(
        ...,
        description="Fecha de emisión del comprobante (YYYY-MM-DD)"
    )
    moneda: str = Field(
        default="PEN",
        description="Moneda del comprobante: PEN o USD"
    )
    monto_total: Decimal = Field(
        ...,
        gt=0,
        description="Importe total facturado"
    )


class ActivoExtraido(BaseModel):
    """Bien tangible clasificado como Activo Fijo sujeto a inventario y depreciación."""
    model_config = ConfigDict(str_strip_whitespace=True)

    descripcion: str = Field(
        ...,
        description="Descripción detallada del activo (ej: Laptop Dell Latitude 5440 Core i7)"
    )
    marca: Optional[str] = Field(None, description="Marca del bien (ej: Dell, Lenovo, HP, Toyota)")
    modelo: Optional[str] = Field(None, description="Modelo comercial o técnico")
    numero_serie: Optional[str] = Field(None, description="Número de serie físico (S/N) si figura")
    costo_unitario: Decimal = Field(
        ...,
        gt=0,
        description="Costo de adquisición unitario sin IGV o según corresponda"
    )
    cantidad: int = Field(
        default=1,
        ge=1,
        description="Cantidad adquirida de este mismo activo"
    )
    categoria_sugerida: str = Field(
        default="Equipos de Cómputo",
        description="Categoría sugerida: Equipos de Cómputo, Maquinaria y Equipo, Equipos de Transporte, Muebles y Enseres, Edificaciones"
    )


class FacturaExtraccionResultado(BaseModel):
    """Estructura completa estricta (JSON Schema) generada por el pipeline de IA."""
    model_config = ConfigDict(str_strip_whitespace=True)

    proveedor: ProveedorExtraido
    documento: DocumentoExtraido
    activos: List[ActivoExtraido] = Field(
        default_factory=list,
        description="Lista de bienes duraderos tangibles extraídos como activos fijos"
    )
    consumibles_descartados: List[str] = Field(
        default_factory=list,
        description="Lista de ítems de la factura descartados por ser suministros o consumibles no inventariables"
    )