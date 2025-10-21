"""
Rutas API para Reportes de Errores
HU05: Reportar inconsistencias
"""
from fastapi import APIRouter, HTTPException
from app.models.reporte_model import ReporteError, ReporteResponse
from app.services.report_service import report_service

router = APIRouter()

@router.post("/crear", response_model=ReporteResponse)
async def crear_reporte(reporte: ReporteError):
    """
    HU05: Crear reporte de error o inconsistencia
    """
    try:
        resultado = await report_service.guardar_reporte(reporte)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear reporte: {str(e)}")

@router.get("/listar")
async def listar_reportes(limit: int = 100):
    """
    Listar reportes guardados
    """
    try:
        reportes = await report_service.obtener_reportes(limit=limit)
        return {"reportes": reportes, "total": len(reportes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar reportes: {str(e)}")
