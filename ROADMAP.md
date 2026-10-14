# ROADMAP - Sistema de Gestión de Activos Fijos (SGAF)

## FASE 1: Inicialización, Abstracción y Persistencia (CLI)
- [x] Tarea 1.1: Inicialización de memoria viva y persistente (`ROADMAP.md`, `STATE.json`, `MEMORY.md`).
- [x] Tarea 1.2: Capa de abstracción semántica (`backend/config/db_schema.py`) y conector dinámico multi-perfil (`backend/config/db_connection.py`).
- [x] Tarea 1.3: DDL y migraciones para las 17 tablas en PostgreSQL con restricciones CHECK, FKs e índices optimizados (`backend/database/ddl.sql` y `backend/database/migrator.py`).
- [x] Tarea 1.4: Semillero de datos iniciales (`backend/database/seed.py`): cuentas PCGE (33, 39, 68), estados de activo y categorías base.
- [x] Tarea 1.5: Interfaz CLI para gestión de base de datos (`cli.py db ping`, `cli.py db switch`, `cli.py db migrate`, `cli.py db seed`).
- [x] Tarea 1.6: Suite de pruebas automatizadas con pytest para persistencia, integridad referencial y restricciones CHECK (`tests/test_phase1_db.py`).

## FASE 2: Ingesta Inteligente de Comprobantes con IA (CLI)
- [x] Tarea 2.1: Módulo de cliente IA con Gemini API (`google-genai`) y esquema estructurado estricto (JSON Schema / Pydantic v2).
- [x] Tarea 2.2: Lógica de filtrado semántico para bienes de activo fijo descartando suministros y consumibles.
- [x] Tarea 2.3: Comando interactivo CLI `python cli.py ingestar-factura --archivo <ruta>` con previsualización en tabla y confirmación/edición interactiva.
- [x] Tarea 2.4: Persistencia transaccional atómica en proveedor, documento_adquisicion y activo_fijo.
- [x] Tarea 2.5: Tests automatizados con mock de comprobante y verificación de integridad en cascada (`tests/test_phase2_ingestion.py`).

## FASE 3: Motor Contable de Depreciación y Liquidación de Bajas (CLI)
- [x] Tarea 3.1: Motor contable de depreciación en línea recta con consideración de mejoras, valor residual y control de bienes totalmente depreciados en uso ($VNL \le Valor Residual \implies Cuota = 0$).
- [x] Tarea 3.2: Control estricto de periodos contables abiertos/cerrados con transacciones atómicas secuenciales.
- [x] Tarea 3.3: Comando CLI `python cli.py depreciacion cerrar-mes --anio <YYYY> --mes <MM>`.
- [x] Tarea 3.4: Motor financiero de bajas (obsolescencia, robo, siniestro con pérdida = VNL; venta con cálculo de ganancia/pérdida = valor venta - VNL) y finalización de asignaciones.
- [x] Tarea 3.5: Comando CLI `python cli.py activo reportar-baja --id <ID> --motivo <MOTIVO> [--precio-venta <VALOR>]`.
- [x] Tarea 3.6: Tests automatizados de simulación de depreciación a 12 meses y liquidación de bajas (`tests/test_phase3_depreciation.py`).

## FASE 4: APIs de Integración y Exportador SUNAT PLE 7.1
- [x] Tarea 4.1: Estructuración de aplicación FastAPI y routers modulares (`backend/main.py`).
- [x] Tarea 4.2: Endpoint `GET /api/v1/integracion/empleados/{id}/activos-asignados` (Custodia patrimonial para RRHH).
- [x] Tarea 4.3: Endpoint `GET /api/v1/integracion/contabilidad/asiento-depreciacion` (Distribución contable para asiento de Diario).
- [x] Tarea 4.4: Endpoints operativos `POST /api/v1/activos/{id}/traslados` y `POST /api/v1/activos/{id}/mantenimientos`.
- [x] Tarea 4.5: Módulo generador y endpoint `GET /api/v1/reportes/ple-7-1` para exportación oficial de Libro Electrónico PLE 7.1 (`.txt`).
- [x] Tarea 4.6: Endpoints de monitoreo y alertas (`GET /api/v1/alertas/vida-util`, `GET /api/v1/alertas/huerfanos`).
- [x] Tarea 4.7: Suite de pruebas de integración HTTP para la API completa (`tests/test_phase4_api.py`).

## FASE 5: Interfaz de Usuario y Experiencia en Next.js
- [x] Tarea 5.1: Inicialización de proyecto Next.js (App Router, Tailwind CSS, Lucide Icons, TanStack Query).
- [x] Tarea 5.2: Dashboard principal con KPIs patrimoniales, alertas y estado general.
- [x] Tarea 5.3: Vista de subida inteligente de facturas (drag & drop, estados de carga IA, formulario de revisión previa).
- [x] Tarea 5.4: Padrón interactivo de activos (búsqueda, filtros, detalle/hoja de vida).
- [x] Tarea 5.5: Consola de depreciación mensual (bloqueo protegido, confirmación modal, barra de progreso y descarga PLE 7.1).
- [x] Tarea 5.6: Módulo y modal de bajas con alerta de impacto financiero en tiempo real.
- [x] Tarea 5.7: Validación visual integral, debouncing, skeletons y protección contra doble envío.

---
## ESTADO DE VERIFICACI?N FINAL (CI/CD)
- [x] Persistencia e Integridad Relacional: 17 tablas en PostgreSQL 16 con verificaci?n de restricciones compuestas.
- [x] Ingesta Inteligente con IA: Extracci?n y discriminaci?n sem?ntica probada con comprobante de muestra y modo mock.
- [x] Motor Contable: Devengo mensual a 12 periodos, control de activos depreciados en uso ($VNL \le residual \implies cuota = 0$) y liquidaciones de baja.
- [x] APIs REST FastAPI: 9 endpoints operativos, exportaci?n SUNAT PLE 7.1 (.txt) y previsualizaci?n de bajas.
- [x] Frontend Next.js: 6 m?dulos visuales construidos con TanStack Query y compilados exitosamente (`npm run build`).
- [x] Pruebas Automatizadas: 24/24 pruebas pasando al 100% (0.97s).
