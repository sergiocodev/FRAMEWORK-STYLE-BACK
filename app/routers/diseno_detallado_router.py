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
