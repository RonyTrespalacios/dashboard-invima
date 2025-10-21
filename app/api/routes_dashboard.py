"""
Rutas API para Dashboard
HU02: Estadísticas y visualizaciones
"""
from fastapi import APIRouter, HTTPException
from app.services.socrata_client import socrata_client

router = APIRouter()

@router.get("/estadisticas")
async def obtener_estadisticas():
    """
    HU02: Obtener estadísticas generales del dashboard
    - Total de trámites
    - Trámites por estado
    - Trámites por mes
    """
    try:
        stats = await socrata_client.obtener_estadisticas()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

@router.get("/metricas")
async def obtener_metricas():
    """
    Métricas adicionales para el dashboard
    """
    try:
        # Total de trámites
        total_data = await socrata_client.query(
            select="COUNT(*) as total",
            limit=1
        )
        
        # Estados únicos
        estados = await socrata_client.query(
            select="DISTINCT estado",
            limit=100
        )
        
        return {
            "total_tramites": int(total_data[0].get("total", 0)) if total_data else 0,
            "estados_disponibles": [e.get("estado") for e in estados if e.get("estado")],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener métricas: {str(e)}")
