from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class CalistaDimensiones(BaseModel):
    score_estetico: Optional[float] = Field(None, description="Puntuación estética en escala 1.00 - 7.00")
    categoria: str = Field("Pendiente", description="Categoría estética: Baja, Media, Alta, Pendiente")
    color_hex: str = Field("#94a3b8", description="Código de color para badges: #ef4444, #f59e0b, #10b981, #94a3b8")
    porcentaje: Optional[float] = Field(None, description="Porcentaje normalizado 0% - 100%")
    balance_visual: Optional[float] = Field(None, description="Equilibrio espacial del peso visual (1.00 - 7.00)")
    armonia_color: Optional[float] = Field(None, description="Cohesión cromática y contraste (1.00 - 7.00)")
    complejidad_espacio: Optional[float] = Field(None, description="Limpieza y proporción de espacio en blanco (1.00 - 7.00)")

class CalistaHallazgoSugerido(BaseModel):
    problema: str
    severidad: str = "mayor"  # critico, mayor, menor
    fase_origen: int = 4
    fase_origen_nombre: str = "Diseño Detallado (Modelo Calista)"
    sugerencia: str

class CalistaPantallaResult(BaseModel):
    pantalla_id: int
    pantalla_nombre: str
    imagen_url: Optional[str] = None
    tiene_imagen: bool = Field(True, description="Indica si la pantalla cuenta con un archivo de captura real en disco")
    score_estetico: Optional[float] = None
    categoria: str  # Baja, Media, Alta, Pendiente
    color_hex: str
    porcentaje: Optional[float] = None
    aprobado: Optional[bool] = None
    diagnostico: str
    dimensiones: Optional[CalistaDimensiones] = None
    recomendaciones: List[str] = []
    hallazgo_sugerido: Optional[CalistaHallazgoSugerido] = None

class CalistaModeloInfo(BaseModel):
    id: str = Field(..., description="Nombre del archivo del modelo (ej: calista_mobilenet_v3.keras)")
    nombre: str = Field(..., description="Nombre amigable para mostrar en UI")
    arquitectura: str = Field(..., description="Tipo de arquitectura: MobileNetV3, CNN Básica, etc.")
    descripcion: str = Field(..., description="Breve descripción del modelo y técnica")
    es_recomendado: bool = False
    es_valido: bool = True
    parametros: Optional[int] = None

class CalistaEvaluacionResponse(BaseModel):
    proyecto_id: int
    score_global: float
    categoria_global: str
    color_global: str
    porcentaje_global: float
    total_pantallas: int
    pantallas_evaluadas_count: int = 0
    pantallas_pendientes_count: int = 0
    aprobadas_count: int
    requieren_ajustes_count: int
    pantallas: List[CalistaPantallaResult] = []
    pantalla_seleccionada: Optional[CalistaPantallaResult] = None
    fecha_analisis: Optional[str] = None
    modelo_activo: Optional[str] = None
    modelos_disponibles: List[CalistaModeloInfo] = []

class CalistaApplyRequest(BaseModel):
    pantalla_id: int
    problema: str
    severidad: str = "mayor"
    fase_origen: int = 4
    fase_origen_nombre: str = "Diseño Detallado (Modelo Calista)"
