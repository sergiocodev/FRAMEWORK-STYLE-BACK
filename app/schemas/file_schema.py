from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArchivoBase(BaseModel):
    proyecto_id: int
    fase_id: Optional[int] = None
    contexto_tipo: Optional[str] = None
    contexto_id: Optional[int] = None
    nombre_original: str
    mime_type: Optional[str] = None
    tamano_bytes: Optional[int] = None

class ArchivoCreate(ArchivoBase):
    ruta_almacenamiento: str
    subido_por: int

class ArchivoResponse(ArchivoBase):
    id: int
    subido_por: int
    subido_en: datetime

    class Config:
        from_attributes = True
