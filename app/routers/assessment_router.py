from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.assessment_schema import (
    EvaluacionResponse,
    EvaluacionUpdate,
    ChecklistItemUpdate,
    HallazgoResponse,
    HallazgoCreate,
    HallazgoUpdate
)
from app.schemas.gestalt_tda_schema import GestaltTdaResponse, TdaApplyRequest
from app.schemas.calista_schema import CalistaEvaluacionResponse, CalistaApplyRequest, CalistaModeloInfo
from app.services import assessment_service, gestalt_tda_service, calista_service

router = APIRouter(
    prefix="/api/v1/proyectos/{proyecto_id}/assessment",
    tags=["Fase 5: Evaluación Estética"]
)

@router.get("", response_model=EvaluacionResponse, summary="Obtener Evaluación Estética")
def get_assessment(proyecto_id: int, db: Session = Depends(get_db)):
    """
    Obtiene la evaluación estética completa de un proyecto.
    Si no existe, se inicializa automáticamente con los valores predeterminados de Gestalt, VisAWI y hallazgos.
    """
    return assessment_service.get_or_create_evaluacion(db, proyecto_id)

@router.put("", response_model=EvaluacionResponse, summary="Actualizar Evaluación Estética")
def update_assessment(proyecto_id: int, eval_in: EvaluacionUpdate, db: Session = Depends(get_db)):
    """
    Actualiza la configuración, método seleccionado, checklist o métricas VisAWI de la evaluación.
    """
    return assessment_service.update_evaluacion(db, proyecto_id, eval_in)

@router.put("/checklist/{item_id}", response_model=EvaluacionResponse, summary="Actualizar ítem heurístico Gestalt")
def update_checklist_item(proyecto_id: int, item_id: str, item_in: ChecklistItemUpdate, db: Session = Depends(get_db)):
    """
    Actualiza el estado gradual (cumple, parcial, no_cumple, no_aplica), notas u observaciones de un principio heurístico.
    """
    return assessment_service.update_checklist_item(db, proyecto_id, item_id, item_in)

@router.put("/checklist/{item_id}/toggle", response_model=EvaluacionResponse, summary="Alternar estado de ítem de checklist")
def toggle_checklist(proyecto_id: int, item_id: str, cumple: Optional[bool] = None, db: Session = Depends(get_db)):
    """
    Alterna o asigna el estado 'cumple' de un principio heurístico específico.
    """
    return assessment_service.toggle_checklist_item(db, proyecto_id, item_id, cumple)

@router.post("/hallazgos", response_model=HallazgoResponse, summary="Agregar un Hallazgo")
def add_finding(proyecto_id: int, hallazgo_in: HallazgoCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo problema detectado en la matriz de hallazgos.
    """
    return assessment_service.add_hallazgo(db, proyecto_id, hallazgo_in)

@router.put("/hallazgos/{hallazgo_id}", response_model=HallazgoResponse, summary="Actualizar un Hallazgo")
def update_finding(proyecto_id: int, hallazgo_id: int, hallazgo_in: HallazgoUpdate, db: Session = Depends(get_db)):
    """
    Modifica la severidad, descripción, estado o fase de origen de un hallazgo existente.
    """
    hallazgo = assessment_service.update_hallazgo(db, hallazgo_id, hallazgo_in)
    if not hallazgo:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    return hallazgo

@router.put("/hallazgos/{hallazgo_id}/toggle-resuelto", response_model=HallazgoResponse, summary="Alternar estado resuelto de un Hallazgo")
def toggle_hallazgo_resuelto(proyecto_id: int, hallazgo_id: int, db: Session = Depends(get_db)):
    """
    Alterna el estado resuelto de un hallazgo (de pendiente a resuelto o viceversa).
    """
    hallazgo = assessment_service.toggle_hallazgo_resuelto(db, hallazgo_id)
    if not hallazgo:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    return hallazgo

@router.delete("/hallazgos/{hallazgo_id}", summary="Eliminar un Hallazgo")
def delete_finding(proyecto_id: int, hallazgo_id: int, db: Session = Depends(get_db)):
    """
    Elimina un hallazgo de la matriz.
    """
    deleted = assessment_service.delete_hallazgo(db, hallazgo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado")
    return {"message": "Hallazgo eliminado correctamente", "id": hallazgo_id}

@router.post("/sync-fase4", response_model=EvaluacionResponse, summary="Sincronizar Alertas de Fase 4")
def sync_fase4(proyecto_id: int, db: Session = Depends(get_db)):
    """
    Importa automáticamente las alertas y no conformidades generadas en la Fase 4 (Diseño Detallado)
    hacia la Matriz de Hallazgos de la Fase 5.
    """
    assessment_service.sync_fase4_alertas_to_hallazgos(db, proyecto_id)
    return assessment_service.get_or_create_evaluacion(db, proyecto_id)

@router.get("/gestalt-tda", response_model=GestaltTdaResponse, summary="Auditoría Topológica Gestalt (TDA)")
@router.post("/gestalt-tda", response_model=GestaltTdaResponse, summary="Auditoría Topológica Gestalt (TDA)")
def run_gestalt_tda(proyecto_id: int, pantalla_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Ejecuta el modelo computacional de Gestalt mediante Homología Persistente (TDA),
    calculando complejos Vietoris-Rips, diagramas 0-PD / 1-PD, Silhouette Scores y evaluando
    las 5 heurísticas de percepción visual (Chen et al., 2025).
    """
    return gestalt_tda_service.analizar_proyecto_gestalt_tda(db, proyecto_id, pantalla_id)

@router.post("/gestalt-tda/aplicar", summary="Aplicar Diagnóstico Topológico a la Evaluación")
def apply_gestalt_tda(proyecto_id: int, request: TdaApplyRequest, db: Session = Depends(get_db)):
    """
    Aplica las puntuaciones del análisis topológico al checklist heurístico de la Fase 5
    e inyecta los defectos detectados en la Matriz de Hallazgos.
    """
    return gestalt_tda_service.aplicar_resultados_tda_a_evaluacion(db, proyecto_id, request)

@router.get("/visawi-questionnaire", summary="Obtener Cuestionario VisAWI Oficial (18 Ítems)")
def get_visawi_questionnaire():
    """
    Retorna los 18 reactivos psicométricos oficiales de Moshagen & Thielsch (2010)
    extraídos de VISAWIdev.xlsx organizados por sus 4 subescalas (Simplicidad, Claridad, Diversidad, Armonía)
    en escala Likert de 1 a 7 puntos.
    """
    return {
        "instrumento": "Visual Aesthetics of Websites Inventory (VisAWI) - Versión Oficial",
        "autores": "Moshagen & Thielsch (2010)",
        "escala": {
            "min": 1,
            "max": 7,
            "tipo": "Likert",
            "etiquetas": [
                {"valor": 1, "etiqueta": "Totalmente en desacuerdo"},
                {"valor": 2, "etiqueta": "En desacuerdo"},
                {"valor": 3, "etiqueta": "Ligeramente en desacuerdo"},
                {"valor": 4, "etiqueta": "Neutral"},
                {"valor": 5, "etiqueta": "Ligeramente de acuerdo"},
                {"valor": 6, "etiqueta": "De acuerdo"},
                {"valor": 7, "etiqueta": "Totalmente de acuerdo"}
            ]
        },
        "dimensiones": [
            {
                "nombre": "Simplicidad",
                "descripcion": "Evaluación de la facilidad de uso y la ausencia de elementos innecesarios que puedan distraer al usuario.",
                "items_count": 5
            },
            {
                "nombre": "Claridad",
                "descripcion": "Evaluación del grado en el que el diseño es claro y comprensible.",
                "items_count": 4
            },
            {
                "nombre": "Diversidad",
                "descripcion": "Evaluación de la variedad y dinamismo en el diseño que mantienen el interés del usuario.",
                "items_count": 5
            },
            {
                "nombre": "Armonía",
                "descripcion": "Evaluación de la cohesión y coherencia de los elementos visuales.",
                "items_count": 4
            }
        ],
        "items": assessment_service.DEFAULT_VISAWI_ITEMS
    }

@router.get("/calista/modelos", response_model=List[CalistaModeloInfo], summary="Listar Modelos Neuronales Calista")
def get_calista_models():
    """
    Lista todos los modelos neuronales disponibles en app/ml_models con sus metadatos.
    """
    return calista_service.listar_modelos_calista()

@router.get("/calista", response_model=CalistaEvaluacionResponse, summary="Obtener Evaluación Calista AI")
def get_calista_evaluation(
    proyecto_id: int,
    pantalla_id: Optional[int] = None,
    modelo_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene la evaluación estética calculada por el modelo Calista para las pantallas de Fase 4.
    Permite seleccionar el modelo de inferencia (MobileNetV3, estetic_559.h5, etc.).
    """
    return calista_service.analizar_proyecto_calista(db, proyecto_id, pantalla_id, modelo_id)

@router.post("/calista/analizar", response_model=CalistaEvaluacionResponse, summary="Ejecutar Inferencia Calista")
def run_calista_inference(
    proyecto_id: int,
    pantalla_id: Optional[int] = None,
    modelo_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Ejecuta la inferencia neuronal sobre la pantalla seleccionada de Fase 4 usando el modelo seleccionado.
    """
    return calista_service.analizar_proyecto_calista(db, proyecto_id, pantalla_id, modelo_id)

@router.post("/calista/aplicar", summary="Aplicar Hallazgo Calista a la Matriz")
def apply_calista_finding(proyecto_id: int, request: CalistaApplyRequest, db: Session = Depends(get_db)):
    """
    Inyecta un hallazgo sugerido por el modelo Calista en la Matriz Central de Hallazgos del proyecto.
    """
    return calista_service.aplicar_calista_hallazgo_a_evaluacion(db, proyecto_id, request)


