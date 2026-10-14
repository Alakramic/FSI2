# MEMORY - Bit?cora T?cnica de Arquitectura y Decisiones (SGAF)

## 1. Decisiones de Arquitectura (ADRs)
- **ADR-001: Arquitectura CLI-First con Schema Adapter**:
  - Toda la persistencia se abstrae en `backend/config/db_schema.py` (`TABLES` y `COLUMNS`) y `backend/config/db_connection.py` (`DB_PROFILE`).
  - La interfaz de consola (`cli.py`) es la primera l?nea de ejecuci?n y validaci?n integral.
- **ADR-002: Modelo de Integridad Relacional Estricta**:
  - PostgreSQL 16 con llaves for?neas expl?citas, `IDENTITY`, restricciones compuestas (`uq_doc_adquisicion`, `uq_depreciacion_activo_periodo`), y verificaciones `CHECK` (`fecha_inicio_uso >= fecha_adquisicion`, `costo > 0`, `origen <> destino`).
- **ADR-003: Motor Contable y Regla de Activos Totalmente Depreciados**:
  - Depreciaci?n en l?nea recta mensual:
    $$\text{Base Depreciable} = \text{Costo Hist?rico} + \sum(\text{Mejoras}) - \text{Valor Residual}$$
    $$\text{Cuota Mensual} = \frac{\text{Base Depreciable}}{\text{Vida ?til en Meses}}$$
    $$\text{VNL} = \text{Base Depreciable} - \text{Depreciaci?n Acumulada}$$
  - Si $\text{VNL} \le \text{Valor Residual}$, cuota mensual calculada $= 0.00$. El activo **permanece en estado EN_USO** en la empresa con estado PLE '9'.
- **ADR-004: Modelo Financiero de Bajas**:
  - Bajas por OBSOLESCENCIA, ROBO o SINIESTRO: P?rdida directa $= VNL$.
  - Bajas por VENTA: Resultado Contable $= \text{Valor Venta} - VNL$ (Ganancia si $>0$, P?rdida si $<0$).
  - Liberaci?n at?mica de custodios en `asignacion_activo` y cambio de estado a PLE '8'.
- **ADR-005: Normativa SUNAT PLE 7.1**:
  - Exportaci?n en formato texto plano `.txt` con delimitador pleca (`|`) para el Registro de Activos Fijos (PLE 7.1). Estructura oficial: `LE[RUC][YYYY]0000070100001111.txt`.
- **ADR-006: Frontend React 19 / Next.js 16 con TanStack Query y Tailwind CSS**:
  - Arquitectura desacoplada en `frontend/` consumiendo FastAPI REST (`http://localhost:8000/api/v1`).
  - Cacheo inteligente, refetching reactivo y microanimaciones de interfaz en modo oscuro.
- **ADR-007: Previsualizaci?n Reactiva de Liquidaciones**:
  - Endpoint `GET /api/v1/activos/{id}/baja/preview` permite c?lculo din?mico previo al registro definitivo de la baja contable.

## 2. Cat?logos Normativos SUNAT
- **Tabla 2**: Tipo de Documento de Identidad (1=DNI, 6=RUC).
- **Tabla 10**: Tipo de Comprobante de Pago (01=Factura, 03=Boleta, 50=DUA).
- **Tabla 13**: Tipo de Cat?logo de Existencias/Activos (3=OSCE, 9=Propio).
- **Tabla 18**: Tipo de Activo Fijo (01=Edificaciones, 02=Maquinaria y Equipo, 03=Equipos de Transporte, 04=Equipos de C?mputo, 05=Muebles y Enseres).
- **Tabla 19**: Estado del Activo Fijo (1=Activo en uso, 2=Temporalmente fuera de uso, 8=Dado de baja, 9=Totalmente depreciado en uso).
- **Tabla 20**: M?todo de Depreciaci?n (1=L?nea Recta).

## 3. Estado de Ejecuci?n
- **Fase 1**: Persistencia & DDL (17 tablas, migradores, seeders, ?ndices B-Tree) -> **Completada [x]**
- **Fase 2**: Ingesta Inteligente con IA (Gemini API & Discriminaci?n Sem?ntica) -> **Completada [x]**
- **Fase 3**: Motor Contable de Depreciaci?n y Liquidaci?n de Bajas -> **Completada [x]**
- **Fase 4**: APIs Desacopladas (FastAPI) y Exportador SUNAT PLE 7.1 -> **Completada [x]**
- **Fase 5**: Interfaz de Usuario Next.js (Dashboard, Ingesta, Padr?n, Depreciaci?n, Bajas, Alertas) -> **Completada [x]**
- **Pruebas Automatizadas**: 23 de 23 pasadas en 0.99s.
- **Build de Producci?n Frontend**: `next build` exitoso con Turbopack.
