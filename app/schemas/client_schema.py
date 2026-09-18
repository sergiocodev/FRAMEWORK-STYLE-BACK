from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ClienteBase(BaseModel):
    nombre: str
    contacto_nombre: Optional[str] = None
    contacto_correo: Optional[EmailStr] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_correo: Optional[EmailStr] = None

class ClienteResponse(ClienteBase):
    id: int
    creado_en: datetime

    class Config:
        from_attributes = True
