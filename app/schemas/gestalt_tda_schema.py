from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class DiagramPoint(BaseModel):
    dimension: int
    birth: float
    death: float
    persistence: float
    is_significant: bool
    proj_dist: float

class SimplexVertex(BaseModel):
    id: int
    x: float
    y: float
    label: Optional[str] = "Elemento"
    cluster_id: int = 0
    color_hex: Optional[str] = "#3b82f6"
    area: float = 1.0

class SimplexEdge(BaseModel):
    source: int
    target: int
    distance: float
    is_continuation: bool = False

class SimplexCycle(BaseModel):
    vertices: List[int]
    persistence: float
    label: str

class HeuristicScore(BaseModel):
    id: str  # c1, c2, c3, c4, c5
    nombre: str
    score: float
    estado: str  # cumple, parcial, no_cumple
    silhouette: float
    diagnostico: str
    recomendacion: str

class ConflictoGestalt(BaseModel):
    tipo: str
    descripcion: str
    dominante: str
    severidad: str

class HallazgoSugerido(BaseModel):
    problema: str
    severidad: str
    fase_origen: int = 4
    fase_origen_nombre: str = "Auditoría Topológica Gestalt"
    heuristica_id: str

class GestaltTdaResponse(BaseModel):
    pantalla_id: Optional[int] = None
    pantalla_nombre: str
    imagen_url: Optional[str] = None
    score_gestalt_global: float
    nivel_cohesion: str
    silhouette_score_0pd: float
    silhouette_score_1pd: float
    epsilon_g_0pd: float
    epsilon_g_1pd: float
    total_componentes: int
    total_lazos: int
    puntos_0pd: List[DiagramPoint] = []
    puntos_1pd: List[DiagramPoint] = []
    vertices: List[SimplexVertex] = []
    aristas: List[SimplexEdge] = []
    ciclos: List[SimplexCycle] = []
    heuristics: List[HeuristicScore] = []
    conflictos: List[ConflictoGestalt] = []
    hallazgos_sugeridos: List[HallazgoSugerido] = []

class TdaApplyRequest(BaseModel):
    pantalla_id: Optional[int] = None
    actualizar_checklist: bool = True
    crear_hallazgos: bool = True
    min_score_hallazgo: float = 75.0
