"""
FastAPI Main Application
Backend para Dashboard INVIMA - Consumo de API Socrata
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import routes_tramites, routes_dashboard, routes_reportes, routes_public

app = FastAPI(
    title="INVIMA Dashboard API",
    description="API para consultar trámites del INVIMA vía Socrata",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    routes_tramites.router,
    prefix=f"{settings.API_PREFIX}/tramites",
    tags=["Trámites"]
)
app.include_router(
    routes_dashboard.router,
    prefix=f"{settings.API_PREFIX}/dashboard",
    tags=["Dashboard"]
)
app.include_router(
    routes_reportes.router,
    prefix=f"{settings.API_PREFIX}/reportes",
    tags=["Reportes"]
)
app.include_router(
    routes_public.router,
    prefix=f"{settings.API_PREFIX}/public",
    tags=["Público"]
)

@app.get("/")
async def root():
    return {
        "message": "INVIMA Dashboard API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
