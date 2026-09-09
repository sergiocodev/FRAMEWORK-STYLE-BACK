from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.models.project_model import TipoProyecto, NivelDiseno, EstadoProyecto

class ClienteResponse(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

class ProyectoBase(BaseModel):
    nombre: str
    tipo: Optional[TipoProyecto] = TipoProyecto.nuevo
    cliente_id: Optional[int] = None
    plataforma: Optional[str] = None
    nivel_diseno_objetivo: Optional[NivelDiseno] = NivelDiseno.medio
    estado: Optional[EstadoProyecto] = EstadoProyecto.en_proceso

class ProyectoCreate(ProyectoBase):
    responsable_id: int

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[TipoProyecto] = None
    cliente_id: Optional[int] = None
    plataforma: Optional[str] = None
    nivel_diseno_objetivo: Optional[NivelDiseno] = None
    estado: Optional[EstadoProyecto] = None
    fase_actual_id: Optional[int] = None
    responsable_id: Optional[int] = None

class ProyectoResponse(ProyectoBase):
    id: int
    fase_actual_id: int
    responsable_id: int
    cliente: Optional[ClienteResponse] = None
    creado_en: datetime
    actualizado_en: Optional[datetime] = None

    class Config:
        from_attributes = True
