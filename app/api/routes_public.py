"""
Rutas API Públicas
HU03: Tablero público
HU04: Datos abiertos
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.services.socrata_client import socrata_client
import io
import csv
import json

router = APIRouter()

@router.get("/tablero")
async def obtener_tablero_publico():
    """
    HU03: Tablero público con resumen de trámites
    """
    try:
        # Obtener estadísticas generales
        stats = await socrata_client.obtener_estadisticas()
        
        # Obtener últimos trámites
        ultimos = await socrata_client.query(
            select="*",
            order="fecha_radicacion DESC",
            limit=10
        )
        
        return {
            "estadisticas": stats,
            "ultimos_tramites": ultimos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tablero público: {str(e)}")

@router.get("/datos-abiertos")
async def obtener_datos_abiertos(
    formato: str = Query("json", regex="^(json|csv)$"),
    limit: int = Query(1000, ge=1, le=10000)
):
    """
    HU04: Descarga de datos abiertos en formato JSON o CSV
    """
    try:
        datos = await socrata_client.obtener_datos_publicos(
            formato=formato,
            limit=limit
        )
        
        if formato == "csv":
            # Convertir a CSV
            if not datos:
                raise HTTPException(status_code=404, detail="No hay datos disponibles")
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=datos[0].keys())
            writer.writeheader()
            writer.writerows(datos)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=invima_datos.csv"}
            )
        else:
            # Retornar JSON
            return {"total": len(datos), "datos": datos}
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos abiertos: {str(e)}")
