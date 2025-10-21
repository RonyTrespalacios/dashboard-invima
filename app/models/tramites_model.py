"""
Modelos de Datos para Trámites
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TramiteBase(BaseModel):
    numero_radicado: Optional[str] = None
    nombre_tramite: Optional[str] = None
    estado: Optional[str] = None
    fecha_radicacion: Optional[str] = None
    
class TramiteSearch(BaseModel):
    radicado: Optional[str] = None
    estado: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class TramiteResponse(BaseModel):
    total: int
    data: List[dict]
    limit: int
    offset: int
