from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Subcriterios
class SubcriterioItemSchema(BaseModel):
    id: str
    titulo: str
    cumple: bool = True

# Checklist items
class ChecklistItemSchema(BaseModel):
    id: str
    titulo: str
    descripcion: str
    cumple: bool = True
    estado: Optional[str] = "cumple"  # cumple, parcial, no_cumple, no_aplica
    observacion: Optional[str] = ""
    evaluado_por_ia: Optional[bool] = False
    pantalla_id: Optional[int] = None
    pantalla_nombre: Optional[str] = None
    subcriterios: Optional[List[SubcriterioItemSchema]] = []

class ChecklistItemUpdate(BaseModel):
    estado: Optional[str] = None
    cumple: Optional[bool] = None
    observacion: Optional[str] = None
    evaluado_por_ia: Optional[bool] = None
    subcriterio_id: Optional[str] = None
    subcriterio_cumple: Optional[bool] = None
    subcriterios: Optional[List[SubcriterioItemSchema]] = None

# VisAWI items
class VisawiMetricaSchema(BaseModel):
    dimension: str
    puntaje: float
    target: Optional[float] = 4.5
    reactivo: Optional[str] = None

class VisawiEncuestaRespuestaInput(BaseModel):
    evaluador_nombre: Optional[str] = "Evaluador Anónimo"
    evaluador_rol: Optional[str] = "Evaluador UX"
    respuestas: Dict[int, int]  # Reactivo ID (1..18) -> Puntuación Likert (1..7)
    reiniciar_muestra: Optional[bool] = False

class VisawiEncuestaResponse(BaseModel):
    id: int
    evaluacion_id: int
    evaluador_nombre: str
    evaluador_rol: str
    respuestas: Dict[str, Any]
    score_simplicidad: float
    score_claridad: float
    score_diversidad: float
    score_armonia: float
    score_global: float
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True

# Hallazgos
class HallazgoBase(BaseModel):
    problema: str
    severidad: str = "mayor"  # critico, mayor, menor
    fase_origen: int = 3
    fase_origen_nombre: str = "Diseño Visual"
    resuelto: bool = False

class HallazgoCreate(HallazgoBase):
    pass

class HallazgoUpdate(BaseModel):
    problema: Optional[str] = None
    severidad: Optional[str] = None
    fase_origen: Optional[int] = None
    fase_origen_nombre: Optional[str] = None
    resuelto: Optional[bool] = None

class HallazgoResponse(HallazgoBase):
    id: int
    evaluacion_id: int
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True

# Evaluacion Estetica
class EvaluacionUpdate(BaseModel):
    metodo_seleccionado: Optional[str] = None
    estado: Optional[str] = None
    encuesta_url: Optional[str] = None
    encuesta_activa: Optional[bool] = None
    encuesta_token: Optional[str] = None
    auto_cerrar_cupo: Optional[bool] = None
    total_respuestas: Optional[int] = None
    respuestas_completadas: Optional[int] = None
    conclusion_estado: Optional[str] = None
    conclusion_texto: Optional[str] = None
    checklist: Optional[Union[List[ChecklistItemSchema], List[Dict[str, Any]], Dict[str, Any], Any]] = None
    visawi_metricas: Optional[Union[List[VisawiMetricaSchema], List[Dict[str, Any]], Dict[str, Any], Any]] = None
    calista_metricas: Optional[Union[Dict[str, Any], Any]] = None
    justificaciones: Optional[Union[List[str], Dict[str, Any], Any]] = None

# Pantallas Fase 4 resumidas para Fase 5
class PantallaFase4Item(BaseModel):
    id: int
    nodo_id: int
    nombre_pantalla: str
    archivo_id: Optional[int] = None
    archivo_url: Optional[str] = None
    estado_diseno: str
    total_alertas: int = 0
    alertas: List[Dict[str, Any]] = []

class EvaluacionResponse(BaseModel):
    id: int
    proyecto_id: int
    metodo_seleccionado: str
    estado: str
    encuesta_url: Optional[str] = None
    total_respuestas: int
    respuestas_completadas: int
    conclusion_estado: str
    conclusion_texto: Optional[str] = None
    checklist: Optional[Union[List[Any], Dict[str, Any], Any]] = None
    visawi_metricas: Optional[Union[List[Any], Dict[str, Any], Any]] = None
    calista_metricas: Optional[Union[Dict[str, Any], Any]] = None
    justificaciones: Optional[Union[List[str], Dict[str, Any], Any]] = None
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    hallazgos: List[HallazgoResponse] = []
    
    # Nuevos campos profesionales de evaluación
    score_estetico: Optional[float] = 0.0
    nivel_madurez: Optional[str] = "En Evaluación"
    pantallas_fase4: List[PantallaFase4Item] = []
    visawi_encuestas: List[VisawiEncuestaResponse] = []
    server_network_ip: Optional[str] = None
    encuesta_activa: bool = True
    encuesta_token: Optional[str] = None
    auto_cerrar_cupo: bool = True
    mensaje_cierre: Optional[str] = None

    class Config:
        from_attributes = True

# Schemas para Encuesta Pública VisAWI Desatendida (Opción B)
class VisawiPublicScreenItem(BaseModel):
    id: int
    nombre_pantalla: str
    archivo_url: Optional[str] = None
    estado_diseno: Optional[str] = "aprobado"

class VisawiPublicQuestionnaireItem(BaseModel):
    id: int
    dimension: str
    pregunta: str
    inverso: bool = False

class VisawiPublicDimensionInfo(BaseModel):
    nombre: str
    descripcion: str
    items_count: int

class VisawiPublicSurveyInfo(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    proyecto_tipo: Optional[str] = None
    pantallas: List[VisawiPublicScreenItem] = []
    dimensiones: List[VisawiPublicDimensionInfo] = []
    items: List[VisawiPublicQuestionnaireItem] = []
    escala: List[Dict[str, Any]] = []
    server_network_ip: Optional[str] = None
    encuesta_activa: bool = True
    encuesta_token: Optional[str] = None
    auto_cerrar_cupo: bool = True
    mensaje_cierre: Optional[str] = None

class VisawiPublicSubmissionResponse(BaseModel):
    success: bool
    mensaje: str
    encuesta_id: int
    evaluador_nombre: str
    evaluador_rol: str
    score_simplicidad: float
    score_claridad: float
    score_diversidad: float
    score_armonia: float
    score_global: float
    total_evaluaciones_proyecto: int

