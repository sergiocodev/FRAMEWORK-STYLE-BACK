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
from app.services import assessment_service

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

@router.post("/auditar-ia", summary="Auditar Prototipos de Fase 4 con IA")
async def auditar_con_ia(proyecto_id: int, db: Session = Depends(get_db)):
    """
    Ejecuta un análisis visual profundo con IA (Gemini Vision) sobre los prototipos de la Fase 4,
    evaluando principios Gestalt, estimando puntuaciones VisAWI y detectando anomalías visuales.
    """
    resultado = await assessment_service.auditar_estetica_con_ia(db, proyecto_id)
    evaluacion_actualizada = assessment_service.get_or_create_evaluacion(db, proyecto_id)
    return {
        "resultado": resultado,
        "evaluacion": evaluacion_actualizada
    }

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


