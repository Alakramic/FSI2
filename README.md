# SGAF Enterprise - Sistema de Gestion de Activos Fijos

Sistema integral de gestion patrimonial y control contable de activos fijos con soporte de inteligencia artificial, devengo de depreciacion lineal bajo NIC 16 y exportacion oficial al Libro PLE 7.1 de la SUNAT.

---

## 1. Arquitectura del Sistema

- **Backend**: FastAPI 0.110+ (Python 3.12), SQLAlchemy 2.0, Pydantic v2.
- **Base de Datos**: PostgreSQL 16 relacional con 17 tablas normalizadas (catalogo SUNAT tabla 18, custodios, ubicaciones, historial de traslados, mantenimientos y periodos contables).
- **Frontend**: Next.js 16 (App Router), React, Tailwind CSS, TanStack Query, Lucide Icons. Diseno corporativo ERP (SAP Fiori / NetSuite).
- **Motor de IA**: Gemini API (google-genai) para procesamiento y discriminacion automatizada de comprobantes (separacion de activos fijos y suministros consumibles).

---

## 2. Requisitos Previos

- Python 3.12 o superior
- Node.js 18 o superior y npm
- PostgreSQL 16 activo
- Clave de API de Google Gemini (opcional para modo mock de IA)

---

## 3. Instalacion y Configuracion

### 3.1 Clonar y configurar variables de entorno

Copiar el archivo de plantilla y configurar las credenciales:

```bash
cp .env.example .env
```

Variables principales en `.env`:
```env
DB_PROFILE=local
DATABASE_URL_LOCAL=postgresql://postgres:postgres@localhost:5432/activos_fijos_db
GEMINI_API_KEY=tu_api_key_aqui
EMPRESA_RUC=20123456789
EMPRESA_RAZON_SOCIAL=CORPORACION PERU S.A.C.
```

### 3.2 Dependencias de Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Dependencias de Frontend

```bash
cd frontend
npm install
cd ..
```

### 3.4 Inicializar Base de Datos

```bash
python cli.py db migrate
python cli.py db seed
```

---

## 4. Ejecucion

El proyecto incluye el lanzador orquestador `play.sh` (Linux/WSL) y `play.ps1` (PowerShell):

```bash
# Iniciar Backend y Frontend en simultaneo
./play.sh

# Opciones individuales
./play.sh backend     # Solo FastAPI (puerto 8000)
./play.sh frontend    # Solo Next.js (puerto 3000)
./play.sh test        # Ejecutar pruebas automatizadas
./play.sh help        # Ver todos los comandos
```

En Windows PowerShell:
```powershell
.\play.ps1
```

- **Frontend Web**: http://localhost:3000
- **Documentacion API (Swagger UI)**: http://localhost:8000/docs

---

## 5. Pruebas Automatizadas

La suite cuenta con 24 pruebas unitarias y de integracion:

```bash
pytest
```

Modulos evaluados:
- `tests/test_phase1_db.py`: Integridad DDL, catalogos SUNAT y relaciones relacionales.
- `tests/test_phase2_ingestion.py`: Validacion de esquemas contables y discriminacion NIC 16.
- `tests/test_phase3_depreciation.py`: Calculo de devengo lineal y generacion PLE 7.1.
- `tests/test_phase4_api.py`: Endpoints REST y control de auditoria preventiva.

---

## 6. Estructura del Repositorio

```
.
├── backend/
│   ├── api/             # Endpoints REST (activos, depreciacion, bajas, alertas, dashboard)
│   ├── config/          # Configuracion de base de datos y esquemas
│   ├── database/        # Migrador DDL y generador de semillero (seed)
│   ├── models/          # Modelos Pydantic y validaciones
│   ├── services/        # Logica de negocio: NIC 16, PLE 7.1, IA Extractor
│   └── main.py          # Punto de entrada de FastAPI
├── frontend/
│   ├── src/
│   │   ├── app/         # Layout principal, tema y configuracion Next.js
│   │   ├── components/  # Vistas modulares del sistema (ERP Dashboard, Padron, etc.)
│   │   └── lib/         # Cliente API y tipos TypeScript
│   └── package.json
├── tests/               # Pruebas automatizadas con pytest
├── cli.py               # Herramienta de consola administrativa
├── play.sh              # Lanzador y orquestador del entorno
├── play.ps1             # Lanzador para Windows PowerShell
├── requirements.txt     # Dependencias de Python
└── .env.example         # Plantilla de variables de entorno
```