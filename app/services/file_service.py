import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.file_model import Archivo

UPLOAD_DIR = "uploads"

# Asegurar que el directorio exista
os.makedirs(UPLOAD_DIR, exist_ok=True)

def upload_file(
    db: Session, 
    file: UploadFile, 
    proyecto_id: int, 
    subido_por: int,
    fase_id: int = None,
    contexto_tipo: str = None,
    contexto_id: int = None
):
    try:
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(file_path)
        
        new_file = Archivo(
            proyecto_id=proyecto_id,
            fase_id=fase_id,
            contexto_tipo=contexto_tipo,
            contexto_id=contexto_id,
            nombre_original=file.filename,
            ruta_almacenamiento=file_path,
            mime_type=file.content_type,
            tamano_bytes=file_size,
            subido_por=subido_por
        )
        
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
        
        return new_file
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")


def get_files_by_phase(db: Session, proyecto_id: int, fase_id: int, contexto_tipo: str = None):
    query = db.query(Archivo).filter(
        Archivo.proyecto_id == proyecto_id,
        Archivo.fase_id == fase_id
    )
    if contexto_tipo:
        query = query.filter(Archivo.contexto_tipo == contexto_tipo)
    return query.all()

