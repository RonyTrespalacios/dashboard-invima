"""
Rutas API para Dashboard
HU02: Estadísticas y visualizaciones
HU-INVIMA-002: Visualización de estadísticas de trámites INVIMA
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
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

@router.get("/estadisticas-suit")
async def obtener_estadisticas_suit(
    ano: Optional[str] = Query(None, description="Filtrar por año"),
    clase: Optional[str] = Query(None, description="Filtrar por clase de trámite"),
    palabra_clave: Optional[str] = Query(None, description="Filtrar por palabra clave en nombre")
):
    """
    HU-INVIMA-002: Visualización de estadísticas de trámites del INVIMA
    
    **Historia de Usuario:**
    Como analista de políticas públicas, quiero visualizar estadísticas sobre los 
    trámites del INVIMA, para identificar tendencias y patrones en el volumen y 
    tipo de trámites registrados.
    
    **Criterios de Aceptación:**
    - Gráficos por año: Barras o líneas con número de trámites por año
    - Gráficos por categoría: Distribución por tipo o clase
    - Exportación: Permitir exportar a PDF o Excel
    - Filtros: Combinables por Año, Clase y palabra clave
    
    **Criterios No Funcionales:**
    - Cálculo directo sobre datos del SUIT
    - Generación de gráficos <5 segundos (hasta 10,000 registros)
    - Interfaz intuitiva y móvil
    """
    try:
        stats = await socrata_client.obtener_estadisticas_suit(
            ano=ano,
            clase=clase,
            palabra_clave=palabra_clave
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas SUIT: {str(e)}"
        )
