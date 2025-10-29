"""
Servicio para manejo de reportes de errores
Almacena todos los reportes en un único archivo JSON: reports/reportes.json
"""
from typing import Dict, List
from datetime import datetime
import json
from pathlib import Path
from app.models.reporte_model import ReporteError
import asyncio

class ReportService:
    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.reports_file = self.reports_dir / "reportes.json"
        self._lock = asyncio.Lock()
        
        # Crear archivo si no existe
        if not self.reports_file.exists():
            with open(self.reports_file, "w", encoding="utf-8") as f:
                json.dump([], f)
    
    async def _leer_reportes(self) -> List[Dict]:
        """Lee todos los reportes del archivo JSON único"""
        try:
            with open(self.reports_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    async def _escribir_reportes(self, reportes: List[Dict]) -> None:
        """Escribe todos los reportes al archivo JSON único"""
        with open(self.reports_file, "w", encoding="utf-8") as f:
            json.dump(reportes, f, indent=2, ensure_ascii=False)
    
    async def guardar_reporte(self, reporte: ReporteError) -> Dict:
        """
        HU05: Guardar reporte de error en un único archivo JSON
        Usa lock para evitar condiciones de carrera en escrituras concurrentes
        """
        async with self._lock:  # Proteger lectura/escritura concurrente
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                reporte_id = f"REP_{timestamp}"
                
                # Leer reportes existentes
                reportes = await self._leer_reportes()
                
                # Preparar nuevo reporte
                reporte_dict = reporte.model_dump()
                reporte_dict["fecha_reporte"] = reporte_dict["fecha_reporte"].isoformat()
                reporte_dict["reporte_id"] = reporte_id
                
                # Agregar al inicio de la lista (más reciente primero)
                reportes.insert(0, reporte_dict)
                
                # Guardar todos los reportes
                await self._escribir_reportes(reportes)
                
                return {
                    "success": True,
                    "message": "Reporte guardado exitosamente",
                    "reporte_id": reporte_id
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Error al guardar reporte: {str(e)}",
                    "reporte_id": None
                }
    
    async def obtener_reportes(self, limit: int = 100) -> list:
        """
        Obtiene lista de reportes desde el archivo único JSON
        Los reportes ya están ordenados por fecha (más reciente primero)
        """
        async with self._lock:
            reportes = await self._leer_reportes()
            return reportes[:limit]

report_service = ReportService()
