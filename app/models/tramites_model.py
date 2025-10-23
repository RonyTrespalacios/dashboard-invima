"""
Modelos de Datos para Trámites
"""
from pydantic import BaseModel, Field
from typing import Optional, List

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

class TramiteSuitStep(BaseModel):
    orden_paso: Optional[str] = None
    descripcion_paso: Optional[str] = None
    orden_condicion: Optional[str] = None
    tipo_accion_condicion: Optional[str] = None
    documento_nombre: Optional[str] = None
    documento_tipo: Optional[str] = None
    descripcion_del_pago: Optional[str] = None

class TramiteSuitItem(BaseModel):
    numero_unico: str
    nombre_tramite: Optional[str] = None
    nombre_comun: Optional[str] = None
    proposito: Optional[str] = None
    nombre_resultado: Optional[str] = None
    clase: Optional[str] = None
    entidad: Optional[str] = None
    fecha_actualizacion: Optional[str] = None
    categorias: List[str] = Field(default_factory=list)
    pasos: List[TramiteSuitStep] = Field(default_factory=list)

class TramiteSuitResponse(BaseModel):
    total: int
    limit: int
    offset: int
    tramites: List[TramiteSuitItem]
