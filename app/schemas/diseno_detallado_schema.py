from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class DisenoDetalladoAlertaSchema(BaseModel):
    id: Optional[int] = None
    tipo: str
    elemento: str
    mensaje: str
    detectado: Optional[str] = None
    esperado: Optional[str] = None

    class Config:
        from_attributes = True

class DisenoDetalladoChecklistSchema(BaseModel):
    id: Optional[int] = None
    pregunta: str
    estado: str

    class Config:
        from_attributes = True

class DisenoDetalladoArchivoResponse(BaseModel):
    id: int
    nodo_id: int
    archivo_id: int
    estado: str
    alertas: List[DisenoDetalladoAlertaSchema] = []
    checklists: List[DisenoDetalladoChecklistSchema] = []
    archivo_url: Optional[str] = None

    class Config:
        from_attributes = True
