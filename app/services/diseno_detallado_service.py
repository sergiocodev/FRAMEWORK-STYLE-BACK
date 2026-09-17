import asyncio
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models.diseno_detallado_model import DisenoDetalladoArchivo, DisenoDetalladoAlerta, DisenoDetalladoChecklistItem, EstadoDiseno, TipoAlerta
from app.models.file_model import Archivo
import uuid
import os
import shutil

UPLOAD_DIR = "uploads/diseno_detallado/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def upload_and_analyze_design(db: Session, proyecto_id: int, nodo_id: int, file: UploadFile):
    # Guardar archivo fisicamente
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Registrar archivo en DB
    db_archivo = Archivo(
        nombre=file.filename,
        ruta=file_path,
        tipo=file.content_type,
        tamanio=os.path.getsize(file_path)
    )
    db.add(db_archivo)
    db.commit()
    db.refresh(db_archivo)

    # Eliminar disenio anterior si existe para este nodo
    existing_diseno = db.query(DisenoDetalladoArchivo).filter(DisenoDetalladoArchivo.nodo_id == nodo_id).first()
    if existing_diseno:
        db.delete(existing_diseno)
        db.commit()

    # Registrar Diseno
    db_diseno = DisenoDetalladoArchivo(
        nodo_id=nodo_id,
        archivo_id=db_archivo.id,
        estado=EstadoDiseno.en_revision
    )
    db.add(db_diseno)
    db.commit()
    db.refresh(db_diseno)

    # Simular analisis de IA
    await simulate_ai_analysis(db, db_diseno.id)
    
    db.refresh(db_diseno)
    return db_diseno

async def simulate_ai_analysis(db: Session, diseno_id: int):
    # Simula el retraso de la red / procesamiento de LLM
    await asyncio.sleep(2)
    
    alertas = [
        DisenoDetalladoAlerta(
            diseno_archivo_id=diseno_id,
            tipo=TipoAlerta.error,
            elemento="Botón primario",
            mensaje="El botón primario no coincide con el color corporativo definido en la guía visual.",
            detectado="#3B82F6",
            esperado="#FF5733"
        ),
        DisenoDetalladoAlerta(
            diseno_archivo_id=diseno_id,
            tipo=TipoAlerta.warning,
            elemento="Espaciado (Padding)",
            mensaje="El espaciado de las tarjetas es inconsistente.",
            detectado="12px",
            esperado="16px"
        )
    ]
    
    checklists = [
        DisenoDetalladoChecklistItem(
            diseno_archivo_id=diseno_id,
            pregunta="Colores aplicados correctamente",
            estado="pendiente"
        ),
        DisenoDetalladoChecklistItem(
            diseno_archivo_id=diseno_id,
            pregunta="Tipografías aplicadas correctamente",
            estado="aceptado"
        ),
        DisenoDetalladoChecklistItem(
            diseno_archivo_id=diseno_id,
            pregunta="Iconografía aplicada correctamente",
            estado="aceptado"
        ),
        DisenoDetalladoChecklistItem(
            diseno_archivo_id=diseno_id,
            pregunta="Espaciado y alineación correcta",
            estado="pendiente"
        )
    ]

    for alerta in alertas:
        db.add(alerta)
    for check in checklists:
        db.add(check)
        
    db.commit()

def get_screen_design(db: Session, nodo_id: int):
    return db.query(DisenoDetalladoArchivo).filter(DisenoDetalladoArchivo.nodo_id == nodo_id).first()

def delete_design(db: Session, nodo_id: int):
    diseno = db.query(DisenoDetalladoArchivo).filter(DisenoDetalladoArchivo.nodo_id == nodo_id).first()
    if diseno:
        db.delete(diseno)
        db.commit()
        return True
    return False
