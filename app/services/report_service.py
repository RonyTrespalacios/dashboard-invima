"""
Servicio para manejo de reportes de errores
"""
from typing import Dict
from datetime import datetime
import json
from pathlib import Path
from app.models.reporte_model import ReporteError

class ReportService:
    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    async def guardar_reporte(self, reporte: ReporteError) -> Dict:
        """
        HU05: Guardar reporte de error
        En producción, esto podría guardar en una BD o enviar email
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reporte_id = f"REP_{timestamp}"
            
            filename = self.reports_dir / f"{reporte_id}.json"
            
            reporte_dict = reporte.model_dump()
            reporte_dict["fecha_reporte"] = reporte_dict["fecha_reporte"].isoformat()
            reporte_dict["reporte_id"] = reporte_id
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(reporte_dict, f, indent=2, ensure_ascii=False)
            
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
        Obtiene lista de reportes guardados
        """
        reportes = []
        for file in sorted(self.reports_dir.glob("REP_*.json"), reverse=True)[:limit]:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    reportes.append(json.load(f))
            except Exception:
                continue
        return reportes

report_service = ReportService()
