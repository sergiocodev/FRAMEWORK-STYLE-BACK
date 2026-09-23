from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.file_schema import ArchivoResponse

# --- INFORME ---
class InvestigacionInformeBase(BaseModel):
    problema: Optional[str] = None
    objetivo: Optional[str] = None
    producto: Optional[str] = None
    expectativas: Optional[str] = None
    referencias: Optional[Dict[str, Any]] = None
    analisis_actual: Optional[str] = None
    restricciones: Optional[str] = None
    identidad_marca: Optional[Dict[str, Any]] = None
    conclusiones_fase2: Optional[str] = None

class InvestigacionInformeCreate(InvestigacionInformeBase):
    pass

class InvestigacionInformeResponse(InvestigacionInformeBase):
    proyecto_id: int
    actualizado_en: datetime

    class Config:
        from_attributes = True

# --- ARQUETIPO NECESIDADES ---
class ArquetipoNecesidadBase(BaseModel):
    descripcion: str
    orden: Optional[int] = 0

class ArquetipoNecesidadCreate(ArquetipoNecesidadBase):
    pass

class ArquetipoNecesidadResponse(ArquetipoNecesidadBase):
    id: int
    arquetipo_id: int

    class Config:
        from_attributes = True

# --- ARQUETIPOS ---
class ArquetipoUsuarioBase(BaseModel):
    nombre: str = Field(..., description="Nombre del perfil de usuario (ej. 'Estudiante', 'Docente'). Es un personaje ficticio que representa a tus usuarios reales y sus comportamientos.")
    etiqueta: Optional[str] = Field(None, description="Nivel de prioridad o rol del usuario (ej. 'Principal', 'Secundario').")
    orden: Optional[int] = Field(0, description="Posición en la que se mostrará en la lista.")

class ArquetipoUsuarioCreate(ArquetipoUsuarioBase):
    necesidades: Optional[List[ArquetipoNecesidadCreate]] = []

class ArquetipoUsuarioUpdate(ArquetipoUsuarioBase):
    avatar_archivo_id: Optional[int] = None
    avatar_url: Optional[str] = None
    necesidades: Optional[List[ArquetipoNecesidadCreate]] = []

class ArquetipoUsuarioResponse(ArquetipoUsuarioBase):
    id: int
    proyecto_id: int
    avatar_archivo_id: Optional[int] = None
    avatar_url: Optional[str] = None
    necesidades: List[ArquetipoNecesidadResponse] = []

    class Config:
        from_attributes = True
