"""
backend/main.py
Punto de Entrada Principal de la API REST - Sistema de Gestión de Activos Fijos (SGAF).
Expone servicios para RRHH, Contabilidad, Operaciones y Exportación SUNAT PLE 7.1.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.integracion import router as integracion_router
from backend.api.activos import router as activos_router
from backend.api.reportes import router as reportes_router
from backend.api.alertas import router as alertas_router
from backend.api.dashboard import router as dashboard_router
from backend.api.catalogos import router as catalogos_router
from backend.api.ingesta import router as ingesta_router
from backend.api.depreciacion_endpoints import router as depreciacion_router
from backend.config.db_connection import ping_db

app = FastAPI(
    title="SGAF API - Sistema de Gestión de Activos Fijos",
    description="Núcleo patrimonial y contable de activos fijos, trazabilidad y cumplimiento SUNAT PLE 7.1",
    version="1.0.0",
)

# Configurar CORS para permitir conexión desde el frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar Routers con prefijo /api/v1
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(catalogos_router, prefix="/api/v1")
app.include_router(ingesta_router, prefix="/api/v1")
app.include_router(depreciacion_router, prefix="/api/v1")
app.include_router(integracion_router, prefix="/api/v1")
app.include_router(activos_router, prefix="/api/v1")
app.include_router(reportes_router, prefix="/api/v1")
app.include_router(alertas_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
def health_check():
    """Diagnóstico de salud de la API y conectividad con la base de datos."""
    db_status = ping_db()
    return {
        "status": "healthy" if db_status["status"] == "ok" else "unhealthy",
        "app": "SGAF Backend",
        "database": db_status,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)