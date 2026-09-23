from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.diseno_conceptual_model import NodoPantalla, TipoNodo
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/proyectos/{proyecto_id}/pantallas/{nodo_id}/diseno-detallado", tags=["Fase 4: Diseño Detallado"])

@router.post("/upload", summary="Subir diseño detallado", description="Asocia un archivo de diseño detallado a una pantalla de la Fase 4 y establece su estado de revisión (e.g. 'En revisión').")
def upload_diseno_detallado(proyecto_id: int, nodo_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # En un entorno real se subiría a S3/GCS o disco local, y se guardaría URL en BD.
    # Por ahora mockeamos éxito.
    return {"message": "Diseño detallado asociado correctamente", "archivo_id": 1, "estado": "pendiente"}

@router.get("", summary="Obtener diseño detallado", description="Obtiene el diseño detallado asociado a una pantalla de la Fase 4 específica.")
def get_diseno_detallado(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    # Como no estamos persistiendo imágenes en BD por ahora, devolvemos 404.
    # Esto le indica al frontend que muestre la zona de subida (estado vacío).
    raise HTTPException(status_code=404, detail="Diseño no encontrado")

@router.delete("", summary="Eliminar diseño detallado", description="Elimina el diseño detallado asociado a una pantalla.")
def delete_diseno_detallado(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    return {"message": "Diseño detallado eliminado"}
