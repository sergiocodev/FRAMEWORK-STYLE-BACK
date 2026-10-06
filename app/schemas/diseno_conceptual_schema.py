from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.diseno_conceptual_model import TipoNodo, EstadoVerificacion, TipoConexion, TipoContenido, PrioridadContenido, OrigenChecklist, EstadoChecklist
from app.schemas.file_schema import ArchivoResponse

# --- CONTENIDOS ---
class ContenidoItemBase(BaseModel):
    tipo: TipoContenido
    nombre: str
    detalle: Optional[str] = None
    prioridad: Optional[PrioridadContenido] = PrioridadContenido.media
    archivo_id: Optional[int] = None
    orden: Optional[int] = 0

class ContenidoItemCreate(ContenidoItemBase):
    pass

class ContenidoItemResponse(ContenidoItemBase):
    id: int
    proyecto_id: int
    nodo_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- NODOS (PANTALLAS) ---
class NodoPantallaBase(BaseModel):
    nombre: str
    tipo: Optional[TipoNodo] = TipoNodo.pantalla
    icono: Optional[str] = None
    descripcion: Optional[str] = None
    pos_x: Optional[int] = 0
    pos_y: Optional[int] = 0
    prioridad: Optional[str] = None
    estado_verificacion: Optional[EstadoVerificacion] = EstadoVerificacion.pendiente
    enlace_diseno_externo: Optional[str] = None

class NodoPantallaCreate(NodoPantallaBase):
    contenidos: Optional[List[ContenidoItemCreate]] = []

class NodoPantallaUpdate(NodoPantallaBase):
    contenidos: Optional[List[ContenidoItemCreate]] = []

class NodoPantallaResponse(NodoPantallaBase):
    id: int
    proyecto_id: int
    creado_en: datetime
    actualizado_en: datetime
    contenidos: List[ContenidoItemResponse] = []

    class Config:
        from_attributes = True

# --- CONEXIONES ---
class NodoConexionBase(BaseModel):
    nodo_origen_id: int
    nodo_destino_id: int
    tipo_conexion: Optional[TipoConexion] = TipoConexion.navegacion

class NodoConexionCreate(NodoConexionBase):
    pass

class NodoConexionResponse(NodoConexionBase):
    id: int
    proyecto_id: int

    class Config:
        from_attributes = True

# --- WIREFRAMES CHECKLIST ---
class WireframeChecklistItemBase(BaseModel):
    pregunta: str
    origen: Optional[OrigenChecklist] = OrigenChecklist.ia
    estado: Optional[EstadoChecklist] = EstadoChecklist.pendiente

class WireframeChecklistItemCreate(WireframeChecklistItemBase):
    pass

class WireframeChecklistItemResponse(WireframeChecklistItemBase):
    id: int
    wireframe_id: int
    creado_en: datetime

    class Config:
        from_attributes = True

# --- WIREFRAMES ---
class WireframeBase(BaseModel):
    nodo_id: Optional[int] = None
    archivo_id: int
    version: Optional[str] = 'v1'
    generado_por_ia: Optional[bool] = False

class WireframeCreate(WireframeBase):
    pass

class WireframeResponse(WireframeBase):
    id: int
    proyecto_id: int
    creado_en: datetime
    checklist_items: List[WireframeChecklistItemResponse] = []
    archivo_url: Optional[str] = None
    fileName: Optional[str] = None

    class Config:
        from_attributes = True


# --- INVENTARIO UPDATE ---
class ContenidoItemUpdate(BaseModel):
    nodo_id: Optional[int] = None
    nombre: Optional[str] = None
    detalle: Optional[str] = None
    prioridad: Optional[PrioridadContenido] = None
    orden: Optional[int] = None

# --- PHASE 2 CHECKLIST ---
class DisenoConceptualChecklistItemBase(BaseModel):
    pregunta: str
    origen: Optional[OrigenChecklist] = OrigenChecklist.ia
    estado: Optional[EstadoChecklist] = EstadoChecklist.pendiente

class DisenoConceptualChecklistItemCreate(DisenoConceptualChecklistItemBase):
    pass

class DisenoConceptualChecklistItemUpdate(BaseModel):
    pregunta: Optional[str] = None
    estado: Optional[EstadoChecklist] = None

class DisenoConceptualChecklistItemResponse(DisenoConceptualChecklistItemBase):
    id: int
    proyecto_id: int
    creado_en: datetime

    class Config:
        from_attributes = True

# --- WIREFRAME CHECKLIST UPDATE ---
class WireframeChecklistItemUpdate(BaseModel):
    pregunta: Optional[str] = None
    estado: Optional[EstadoChecklist] = None

