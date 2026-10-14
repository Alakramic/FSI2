-- ============================================================================
-- SISTEMA DE GESTIÓN DE ACTIVOS FIJOS (SGAF)
-- Script DDL Oficial para PostgreSQL 14+
-- 17 Tablas con Integridad Referencial Estricta, Restricciones CHECK e Índices
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CATÁLOGOS BASE
-- ----------------------------------------------------------------------------

-- 1.1 Catálogo de Cuentas Contables (Plan Contable General Empresarial - PCGE)
CREATE TABLE IF NOT EXISTS cuenta_contable (
    id_cuenta INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(120) NOT NULL
);

-- 1.2 Categorías de Activos
CREATE TABLE IF NOT EXISTS categoria_activo (
    id_categoria INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    vida_util_meses INT NOT NULL CHECK (vida_util_meses > 0),
    metodo_depreciacion VARCHAR(20) NOT NULL DEFAULT 'LINEA_RECTA',
    tasa_anual NUMERIC(5,2) NOT NULL CHECK (tasa_anual >= 0),
    id_cuenta_activo INT NOT NULL REFERENCES cuenta_contable(id_cuenta),
    id_cuenta_dep_acum INT NOT NULL REFERENCES cuenta_contable(id_cuenta),
    id_cuenta_gasto INT NOT NULL REFERENCES cuenta_contable(id_cuenta)
);

-- 1.3 Ubicaciones Físicas y Jerarquías
CREATE TABLE IF NOT EXISTS ubicacion (
    id_ubicacion INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    sede VARCHAR(80) NOT NULL,
    id_ubicacion_padre INT REFERENCES ubicacion(id_ubicacion)
);

-- 1.4 Centros de Costo
CREATE TABLE IF NOT EXISTS centro_costo (
    id_centro_costo INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL
);

-- 1.5 Proveedores
CREATE TABLE IF NOT EXISTS proveedor (
    id_proveedor INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo_documento VARCHAR(2) NOT NULL CHECK (tipo_documento IN ('6', '1')), -- 6: RUC, 1: DNI (Tabla 2 SUNAT)
    ruc CHAR(11) NOT NULL UNIQUE,
    razon_social VARCHAR(150) NOT NULL,
    telefono VARCHAR(20),
    email VARCHAR(100)
);

-- 1.6 Empleados / Custodios
CREATE TABLE IF NOT EXISTS empleado (
    id_empleado INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dni CHAR(8) NOT NULL UNIQUE,
    nombres VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80) NOT NULL,
    cargo VARCHAR(80) NOT NULL,
    id_centro_costo INT NOT NULL REFERENCES centro_costo(id_centro_costo)
);

-- 1.7 Estados del Activo
CREATE TABLE IF NOT EXISTS estado_activo (
    id_estado INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE CHECK (nombre IN ('EN_USO', 'EN_MANTENIMIENTO', 'DADO_DE_BAJA', 'VENDIDO'))
);

-- ----------------------------------------------------------------------------
-- 2. NÚCLEO PATRIMONIAL
-- ----------------------------------------------------------------------------

-- 2.1 Documentos de Adquisición (Facturas, Boletas, DUA, etc.)
CREATE TABLE IF NOT EXISTS documento_adquisicion (
    id_documento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_proveedor INT NOT NULL REFERENCES proveedor(id_proveedor),
    tipo_documento VARCHAR(20) NOT NULL CHECK (tipo_documento IN ('FACTURA', 'BOLETA', 'GUIA', 'ORDEN_COMPRA')),
    tipo_comprobante VARCHAR(2) NOT NULL DEFAULT '01', -- Tabla 10 SUNAT: '01'=Factura, '03'=Boleta, '50'=DUA
    numero VARCHAR(30) NOT NULL,
    fecha_emision DATE NOT NULL,
    moneda CHAR(3) NOT NULL CHECK (moneda IN ('PEN', 'USD')),
    monto_total NUMERIC(14,2) NOT NULL CHECK (monto_total >= 0),
    CONSTRAINT uq_doc_adquisicion UNIQUE (id_proveedor, tipo_documento, numero)
);

-- 2.2 Activos Fijos
CREATE TABLE IF NOT EXISTS activo_fijo (
    id_activo INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE, -- Código patrimonial / etiqueta
    catalogo_tipo_id VARCHAR(2) NOT NULL DEFAULT '9', -- Tabla 13 SUNAT: '3'=OSCE, '9'=Propio
    codigo_osce VARCHAR(16),
    tipo_activo_ple VARCHAR(2) NOT NULL DEFAULT '01', -- Tabla 18 SUNAT
    estado_activo_ple CHAR(1) NOT NULL DEFAULT '1', -- Tabla 19 SUNAT: '1'=En uso, '8'=Baja, '9'=Depreciado
    descripcion VARCHAR(200) NOT NULL,
    marca VARCHAR(60),
    modelo VARCHAR(60),
    numero_serie VARCHAR(60),
    id_categoria INT NOT NULL REFERENCES categoria_activo(id_categoria),
    id_estado INT NOT NULL REFERENCES estado_activo(id_estado),
    id_ubicacion INT NOT NULL REFERENCES ubicacion(id_ubicacion),
    id_centro_costo INT NOT NULL REFERENCES centro_costo(id_centro_costo),
    id_responsable INT NOT NULL REFERENCES empleado(id_empleado),
    id_documento INT NOT NULL REFERENCES documento_adquisicion(id_documento),
    fecha_adquisicion DATE NOT NULL,
    fecha_inicio_uso DATE NOT NULL,
    costo_adquisicion NUMERIC(14,2) NOT NULL CHECK (costo_adquisicion > 0),
    valor_residual NUMERIC(14,2) NOT NULL DEFAULT 0.00 CHECK (valor_residual >= 0),
    vida_util_meses INT NOT NULL CHECK (vida_util_meses > 0),
    metodo_depreciacion VARCHAR(20) NOT NULL DEFAULT '1', -- Tabla 20 SUNAT: '1'=Línea recta
    CONSTRAINT ck_activo_fecha_uso CHECK (fecha_inicio_uso >= fecha_adquisicion)
);

-- ----------------------------------------------------------------------------
-- 3. TRAZABILIDAD Y MOVIMIENTOS
-- ----------------------------------------------------------------------------

-- 3.1 Asignación de Activos a Custodios
CREATE TABLE IF NOT EXISTS asignacion_activo (
    id_asignacion INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_activo INT NOT NULL REFERENCES activo_fijo(id_activo) ON DELETE CASCADE,
    id_empleado INT NOT NULL REFERENCES empleado(id_empleado),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    observacion VARCHAR(200),
    CONSTRAINT ck_asignacion_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_inicio)
);

-- 3.2 Traslado de Activos entre Ubicaciones
CREATE TABLE IF NOT EXISTS traslado_activo (
    id_traslado INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_activo INT NOT NULL REFERENCES activo_fijo(id_activo) ON DELETE CASCADE,
    id_ubicacion_origen INT NOT NULL REFERENCES ubicacion(id_ubicacion),
    id_ubicacion_destino INT NOT NULL REFERENCES ubicacion(id_ubicacion),
    fecha DATE NOT NULL,
    motivo VARCHAR(200) NOT NULL,
    id_autorizado_por INT NOT NULL REFERENCES empleado(id_empleado),
    CONSTRAINT ck_traslado_ubicacion CHECK (id_ubicacion_origen <> id_ubicacion_destino)
);

-- 3.3 Mantenimientos (Preventivo y Correctivo)
CREATE TABLE IF NOT EXISTS mantenimiento (
    id_mantenimiento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_activo INT NOT NULL REFERENCES activo_fijo(id_activo) ON DELETE CASCADE,
    id_proveedor INT REFERENCES proveedor(id_proveedor),
    tipo VARCHAR(15) NOT NULL CHECK (tipo IN ('PREVENTIVO', 'CORRECTIVO')),
    fecha DATE NOT NULL,
    costo NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (costo >= 0),
    descripcion VARCHAR(300) NOT NULL
);

-- 3.4 Mejoras y Capitalizaciones al Activo
CREATE TABLE IF NOT EXISTS mejora_activo (
    id_mejora INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_activo INT NOT NULL REFERENCES activo_fijo(id_activo) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    monto NUMERIC(14,2) NOT NULL CHECK (monto > 0),
    meses_vida_adicional INT NOT NULL DEFAULT 0 CHECK (meses_vida_adicional >= 0)
);

-- 3.5 Revaluaciones Técnicas
CREATE TABLE IF NOT EXISTS revaluacion (
    id_revaluacion INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_activo INT NOT NULL REFERENCES activo_fijo(id_activo) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    valor_anterior NUMERIC(14,2) NOT NULL,
    valor_nuevo NUMERIC(14,2) NOT NULL,
    motivo VARCHAR(200) NOT NULL
);

-- 3.6 Bajas de Activos
CREATE TABLE IF NOT EXISTS baja_activo (
    id_baja INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_activo INT NOT NULL UNIQUE REFERENCES activo_fijo(id_activo) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    motivo VARCHAR(20) NOT NULL CHECK (motivo IN ('OBSOLESCENCIA', 'ROBO', 'SINIESTRO', 'VENTA', 'DONACION')),
    valor_libros NUMERIC(14,2) NOT NULL CHECK (valor_libros >= 0),
    valor_venta NUMERIC(14,2) CHECK (valor_venta IS NULL OR valor_venta >= 0),
    observacion VARCHAR(200)
);

-- ----------------------------------------------------------------------------
-- 4. MOTOR DE DEPRECIACIÓN
-- ----------------------------------------------------------------------------

-- 4.1 Periodos Contables
CREATE TABLE IF NOT EXISTS periodo_contable (
    id_periodo INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    anio SMALLINT NOT NULL,
    mes SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    estado VARCHAR(10) NOT NULL DEFAULT 'ABIERTO' CHECK (estado IN ('ABIERTO', 'CERRADO')),
    CONSTRAINT uq_periodo_anio_mes UNIQUE (anio, mes)
);

-- 4.2 Depreciación Mensual por Activo
CREATE TABLE IF NOT EXISTS depreciacion (
    id_depreciacion INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_activo INT NOT NULL REFERENCES activo_fijo(id_activo) ON DELETE CASCADE,
    id_periodo INT NOT NULL REFERENCES periodo_contable(id_periodo),
    monto_periodo NUMERIC(14,2) NOT NULL CHECK (monto_periodo >= 0),
    depreciacion_acum NUMERIC(14,2) NOT NULL CHECK (depreciacion_acum >= 0),
    valor_neto NUMERIC(14,2) NOT NULL CHECK (valor_neto >= 0),
    CONSTRAINT uq_depreciacion_activo_periodo UNIQUE (id_activo, id_periodo)
);

-- ----------------------------------------------------------------------------
-- 5. ÍNDICES DE RENDIMIENTO Y BÚSQUEDA
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_activo_fijo_codigo ON activo_fijo(codigo);
CREATE INDEX IF NOT EXISTS idx_activo_fijo_categoria ON activo_fijo(id_categoria);
CREATE INDEX IF NOT EXISTS idx_activo_fijo_estado ON activo_fijo(id_estado);
CREATE INDEX IF NOT EXISTS idx_activo_fijo_responsable ON activo_fijo(id_responsable);
CREATE INDEX IF NOT EXISTS idx_activo_fijo_ubicacion ON activo_fijo(id_ubicacion);
CREATE INDEX IF NOT EXISTS idx_activo_fijo_centro_costo ON activo_fijo(id_centro_costo);
CREATE INDEX IF NOT EXISTS idx_activo_fijo_documento ON activo_fijo(id_documento);

CREATE INDEX IF NOT EXISTS idx_asignacion_activo_empleado ON asignacion_activo(id_activo, id_empleado);
CREATE INDEX IF NOT EXISTS idx_traslado_activo ON traslado_activo(id_activo);
CREATE INDEX IF NOT EXISTS idx_mantenimiento_activo ON mantenimiento(id_activo);
CREATE INDEX IF NOT EXISTS idx_mejora_activo ON mejora_activo(id_activo);
CREATE INDEX IF NOT EXISTS idx_revaluacion_activo ON revaluacion(id_activo);

CREATE INDEX IF NOT EXISTS idx_periodo_contable_anio_mes ON periodo_contable(anio, mes);
CREATE INDEX IF NOT EXISTS idx_depreciacion_activo ON depreciacion(id_activo);
CREATE INDEX IF NOT EXISTS idx_depreciacion_periodo ON depreciacion(id_periodo);