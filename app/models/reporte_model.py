"""
Modelos de Datos para Reportes
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class ReporteError(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    tipo_error: str = Field(..., description="Tipo de error encontrado")
    descripcion: str = Field(..., min_length=10, max_length=1000)
    numero_radicado: Optional[str] = None
    fecha_reporte: datetime = Field(default_factory=datetime.now)

class ReporteResponse(BaseModel):
    success: bool
    message: str
    reporte_id: Optional[str] = None
