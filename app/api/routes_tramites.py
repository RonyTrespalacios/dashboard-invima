"""
Rutas API para Trámites
HU01: Búsqueda de trámites
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from app.services.socrata_client import socrata_client
from app.models.tramites_model import TramiteResponse, TramiteSuitResponse

router = APIRouter()

@router.get("/buscar", response_model=TramiteResponse)
async def buscar_tramites(
    radicado: Optional[str] = Query(None, description="Número de radicado"),
    estado: Optional[str] = Query(None, description="Estado del trámite"),
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    HU01: Buscar trámites por diferentes criterios
    """
    try:
        resultado = await socrata_client.buscar_tramites(
            radicado=radicado,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limit=limit,
            offset=offset
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar trámites: {str(e)}")

@router.get("/detalle/{numero_radicado}")
async def obtener_detalle_tramite(numero_radicado: str):
    """
    Obtener detalle de un trámite específico
    """
    try:
        resultado = await socrata_client.buscar_tramites(
            radicado=numero_radicado,
            limit=1
        )
        if resultado["total"] > 0:
            return resultado["data"][0]
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener detalle: {str(e)}")

@router.get("/campos")
async def obtener_campos():
    """
    Obtener lista de campos disponibles en el dataset
    """
    try:
        campos = await socrata_client.obtener_campos()
        return {"campos": campos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener campos: {str(e)}")

@router.get("/suit", response_model=TramiteSuitResponse)
async def buscar_tramites_suit(
    texto: Optional[str] = Query(None, description="Texto libre para buscar por nombre, propósito o palabra clave"),
    categorias: Optional[List[str]] = Query(
        None,
        description="Lista de categorías (ej: medicamentos, alimentos, cosmeticos, dispositivos_medicos, certificaciones)"
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    HU-INVIMA-001: Buscar trámites del INVIMA disponibles en el SUIT.
    """
    try:
        resultado = await socrata_client.buscar_tramites_suit(
            texto=texto,
            categorias=categorias,
            limit=limit,
            offset=offset
        )
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar trámites en el SUIT: {str(e)}")
