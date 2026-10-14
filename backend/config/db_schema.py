"""
backend/config/db_schema.py
Capa de Abstracción Semántica de Base de Datos (Schema Adapter)
Centraliza los nombres de tablas y columnas para evitar cadenas fijas (magic strings)
en repositorios, servicios y consultas SQL.
"""

from typing import Dict, Any

TABLES: Dict[str, str] = {
    "CUENTA_CONTABLE": "cuenta_contable",
    "CATEGORIA_ACTIVO": "categoria_activo",
    "UBICACION": "ubicacion",
    "CENTRO_COSTO": "centro_costo",
    "PROVEEDOR": "proveedor",
    "EMPLEADO": "empleado",
    "ESTADO_ACTIVO": "estado_activo",
    "DOCUMENTO_ADQUISICION": "documento_adquisicion",
    "ACTIVO_FIJO": "activo_fijo",
    "ASIGNACION_ACTIVO": "asignacion_activo",
    "TRASLADO_ACTIVO": "traslado_activo",
    "MANTENIMIENTO": "mantenimiento",
    "MEJORA_ACTIVO": "mejora_activo",
    "REVALUACION": "revaluacion",
    "BAJA_ACTIVO": "baja_activo",
    "PERIODO_CONTABLE": "periodo_contable",
    "DEPRECIACION": "depreciacion",
}

COLUMNS: Dict[str, Dict[str, str]] = {
    "CUENTA_CONTABLE": {
        "ID": "id_cuenta",
        "CODIGO": "codigo",
        "NOMBRE": "nombre",
    },
    "CATEGORIA_ACTIVO": {
        "ID": "id_categoria",
        "NOMBRE": "nombre",
        "VIDA_UTIL_MESES": "vida_util_meses",
        "METODO_DEPRECIACION": "metodo_depreciacion",
        "TASA_ANUAL": "tasa_anual",
        "ID_CUENTA_ACTIVO": "id_cuenta_activo",
        "ID_CUENTA_DEP_ACUM": "id_cuenta_dep_acum",
        "ID_CUENTA_GASTO": "id_cuenta_gasto",
    },
    "UBICACION": {
        "ID": "id_ubicacion",
        "NOMBRE": "nombre",
        "SEDE": "sede",
        "ID_UBICACION_PADRE": "id_ubicacion_padre",
    },
    "CENTRO_COSTO": {
        "ID": "id_centro_costo",
        "CODIGO": "codigo",
        "NOMBRE": "nombre",
    },
    "PROVEEDOR": {
        "ID": "id_proveedor",
        "TIPO_DOCUMENTO": "tipo_documento",
        "RUC": "ruc",
        "RAZON_SOCIAL": "razon_social",
        "TELEFONO": "telefono",
        "EMAIL": "email",
    },
    "EMPLEADO": {
        "ID": "id_empleado",
        "DNI": "dni",
        "NOMBRES": "nombres",
        "APELLIDOS": "apellidos",
        "CARGO": "cargo",
        "ID_CENTRO_COSTO": "id_centro_costo",
    },
    "ESTADO_ACTIVO": {
        "ID": "id_estado",
        "NOMBRE": "nombre",
    },
    "DOCUMENTO_ADQUISICION": {
        "ID": "id_documento",
        "ID_PROVEEDOR": "id_proveedor",
        "TIPO_DOCUMENTO": "tipo_documento",
        "TIPO_COMPROBANTE": "tipo_comprobante",
        "NUMERO": "numero",
        "FECHA_EMISION": "fecha_emision",
        "MONEDA": "moneda",
        "MONTO_TOTAL": "monto_total",
    },
    "ACTIVO_FIJO": {
        "ID": "id_activo",
        "CODIGO": "codigo",
        "CATALOGO_TIPO_ID": "catalogo_tipo_id",
        "CODIGO_OSCE": "codigo_osce",
        "TIPO_ACTIVO_PLE": "tipo_activo_ple",
        "ESTADO_ACTIVO_PLE": "estado_activo_ple",
        "DESCRIPCION": "descripcion",
        "MARCA": "marca",
        "MODELO": "modelo",
        "NUMERO_SERIE": "numero_serie",
        "ID_CATEGORIA": "id_categoria",
        "ID_ESTADO": "id_estado",
        "ID_UBICACION": "id_ubicacion",
        "ID_CENTRO_COSTO": "id_centro_costo",
        "ID_RESPONSABLE": "id_responsable",
        "ID_DOCUMENTO": "id_documento",
        "FECHA_ADQUISICION": "fecha_adquisicion",
        "FECHA_INICIO_USO": "fecha_inicio_uso",
        "COSTO_ADQUISICION": "costo_adquisicion",
        "VALOR_RESIDUAL": "valor_residual",
        "VIDA_UTIL_MESES": "vida_util_meses",
        "METODO_DEPRECIACION": "metodo_depreciacion",
    },
    "ASIGNACION_ACTIVO": {
        "ID": "id_asignacion",
        "ID_ACTIVO": "id_activo",
        "ID_EMPLEADO": "id_empleado",
        "FECHA_INICIO": "fecha_inicio",
        "FECHA_FIN": "fecha_fin",
        "OBSERVACION": "observacion",
    },
    "TRASLADO_ACTIVO": {
        "ID": "id_traslado",
        "ID_ACTIVO": "id_activo",
        "ID_UBICACION_ORIGEN": "id_ubicacion_origen",
        "ID_UBICACION_DESTINO": "id_ubicacion_destino",
        "FECHA": "fecha",
        "MOTIVO": "motivo",
        "ID_AUTORIZADO_POR": "id_autorizado_por",
    },
    "MANTENIMIENTO": {
        "ID": "id_mantenimiento",
        "ID_ACTIVO": "id_activo",
        "ID_PROVEEDOR": "id_proveedor",
        "TIPO": "tipo",
        "FECHA": "fecha",
        "COSTO": "costo",
        "DESCRIPCION": "descripcion",
    },
    "MEJORA_ACTIVO": {
        "ID": "id_mejora",
        "ID_ACTIVO": "id_activo",
        "FECHA": "fecha",
        "DESCRIPCION": "descripcion",
        "MONTO": "monto",
        "MESES_VIDA_ADICIONAL": "meses_vida_adicional",
    },
    "REVALUACION": {
        "ID": "id_revaluacion",
        "ID_ACTIVO": "id_activo",
        "FECHA": "fecha",
        "VALOR_ANTERIOR": "valor_anterior",
        "VALOR_NUEVO": "valor_nuevo",
        "MOTIVO": "motivo",
    },
    "BAJA_ACTIVO": {
        "ID": "id_baja",
        "ID_ACTIVO": "id_activo",
        "FECHA": "fecha",
        "MOTIVO": "motivo",
        "VALOR_LIBROS": "valor_libros",
        "VALOR_VENTA": "valor_venta",
        "OBSERVACION": "observacion",
    },
    "PERIODO_CONTABLE": {
        "ID": "id_periodo",
        "ANIO": "anio",
        "MES": "mes",
        "ESTADO": "estado",
    },
    "DEPRECIACION": {
        "ID": "id_depreciacion",
        "ID_ACTIVO": "id_activo",
        "ID_PERIODO": "id_periodo",
        "MONTO_PERIODO": "monto_periodo",
        "DEPRECIACION_ACUM": "depreciacion_acum",
        "VALOR_NETO": "valor_neto",
    },
}

def t(table_key: str) -> str:
    """Retorna el nombre real de la tabla en base de datos."""
    if table_key not in TABLES:
        raise KeyError(f"Tabla no reconocida en db_schema: {table_key}")
    return TABLES[table_key]

def col(table_key: str, column_key: str) -> str:
    """Retorna el nombre real de la columna para la tabla especificada."""
    if table_key not in COLUMNS:
        raise KeyError(f"Tabla no reconocida en db_schema: {table_key}")
    if column_key not in COLUMNS[table_key]:
        raise KeyError(f"Columna {column_key} no reconocida en tabla {table_key}")
    return COLUMNS[table_key][column_key]