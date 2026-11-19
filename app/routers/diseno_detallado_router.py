from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.diseno_conceptual_model import NodoPantalla, TipoNodo
from app.services import diseno_detallado_service
from pydantic import BaseModel
from typing import List, Optional
import json
import os

router = APIRouter(prefix="/api/proyectos/{proyecto_id}/pantallas/{nodo_id}/diseno-detallado", tags=["Fase 4: Diseño Detallado"])

@router.post("/upload", summary="Subir diseño detallado")
async def upload_diseno_detallado(proyecto_id: int, nodo_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        diseno = await diseno_detallado_service.upload_and_analyze_design(db, proyecto_id, nodo_id, file)
        return get_diseno_detallado(proyecto_id, nodo_id, db)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=traceback.format_exc())

@router.get("", summary="Obtener diseño detallado")
def get_diseno_detallado(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    diseno = diseno_detallado_service.get_screen_design(db, nodo_id)
    if not diseno:
        raise HTTPException(status_code=404, detail="Diseno no encontrado")
    
    # Checklists manually
    from app.models.diseno_detallado_model import DisenoDetalladoChecklistItem
    checklists_db = db.query(DisenoDetalladoChecklistItem).filter(DisenoDetalladoChecklistItem.diseno_archivo_id == diseno.id).all()
    checklists = [{"id": c.id, "pregunta": c.pregunta, "estado": c.estado} for c in checklists_db]
    
    alertas = [{"id": a.id, "tipo": a.tipo, "elemento": a.elemento, "mensaje": a.mensaje} for a in diseno.alertas]
    
    return {
        "id": diseno.id,
        "nodo_id": diseno.nodo_id,
        "archivo_id": diseno.archivo_id,
        "estado": diseno.estado,
        "archivo_url": f"/uploads/diseno_detallado/{os.path.basename(diseno.archivo.ruta_almacenamiento)}",
        "alertas": alertas,
        "checklist": checklists
    }

@router.delete("", summary="Eliminar diseño detallado")
def delete_diseno_detallado(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    success = diseno_detallado_service.delete_design(db, nodo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Diseno no encontrado")
    return {"message": "Diseño detallado eliminado"}

class ChecklistItemUpdate(BaseModel):
    estado: str  # 'aprobado' | 'rechazado' | 'pendiente'

@router.put("/checklist/{item_id}", summary="Actualizar estado de un ítem del checklist de Fase 4")
def update_checklist_item(proyecto_id: int, nodo_id: int, item_id: int, payload: ChecklistItemUpdate, db: Session = Depends(get_db)):
    from app.models.diseno_detallado_model import DisenoDetalladoChecklistItem, EstadoDiseno

    diseno = diseno_detallado_service.get_screen_design(db, nodo_id)
    if not diseno:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")

    item = db.query(DisenoDetalladoChecklistItem).filter(
        DisenoDetalladoChecklistItem.id == item_id,
        DisenoDetalladoChecklistItem.diseno_archivo_id == diseno.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem de checklist no encontrado")

    item.estado = payload.estado
    db.commit()
    db.refresh(item)

    # Recalcular si todos están aprobados
    all_items = db.query(DisenoDetalladoChecklistItem).filter(
        DisenoDetalladoChecklistItem.diseno_archivo_id == diseno.id
    ).all()
    all_approved = len(all_items) > 0 and all(c.estado in ('aprobado', 'aceptado') for c in all_items)
    if all_approved:
        diseno.estado = EstadoDiseno.verificado
    else:
        diseno.estado = EstadoDiseno.en_revision
    db.commit()
    db.refresh(diseno)

    return {
        "id": item.id,
        "pregunta": item.pregunta,
        "estado": item.estado,
        "diseno_estado": diseno.estado.value if hasattr(diseno.estado, 'value') else str(diseno.estado)
    }

class EstadoUpdate(BaseModel):
    estado: str  # 'pendiente' | 'en_revision' | 'verificado'

@router.put("/estado", summary="Actualizar estado de verificación del diseño")
def update_estado_diseno(proyecto_id: int, nodo_id: int, payload: EstadoUpdate, db: Session = Depends(get_db)):
    from app.models.diseno_detallado_model import EstadoDiseno

    diseno = diseno_detallado_service.get_screen_design(db, nodo_id)
    if not diseno:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")

    if payload.estado == "verificado":
        diseno.estado = EstadoDiseno.verificado
    elif payload.estado == "pendiente":
        diseno.estado = EstadoDiseno.pendiente
    else:
        diseno.estado = EstadoDiseno.en_revision

    db.commit()
    db.refresh(diseno)
    return {
        "id": diseno.id,
        "estado": diseno.estado.value if hasattr(diseno.estado, 'value') else str(diseno.estado)
    }

@router.get("/comparativa", summary="Obtener comparativa Wireframe Fase 2 vs Prototipo Fase 4")
def get_comparativa(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    from app.models.diseno_conceptual_model import Wireframe

    diseno = diseno_detallado_service.get_screen_design(db, nodo_id)
    wf = db.query(Wireframe).filter(Wireframe.nodo_id == nodo_id).first()

    wf_url = None
    if wf and wf.archivo:
        wf_url = f"/uploads/wireframes/{os.path.basename(wf.archivo.ruta_almacenamiento)}"

    diseno_url = None
    if diseno and diseno.archivo:
        diseno_url = f"/uploads/diseno_detallado/{os.path.basename(diseno.archivo.ruta_almacenamiento)}"

    return {
        "nodo_id": nodo_id,
        "wireframe_url": wf_url,
        "diseno_url": diseno_url
    }
