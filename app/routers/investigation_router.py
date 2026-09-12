from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
# Suponiendo que tienes dependencia para obtener el usuario actual
# from app.core.security import get_current_user
# Por ahora usaremos un usuario harcodeado o dependecia básica para avanzar
# como `subido_por` es requerido.

from app.schemas import investigation_schema, file_schema
from app.services import investigation_service, file_service

router = APIRouter(
    prefix="/api/v1/proyectos/{proyecto_id}/investigation",
    tags=["Fase 1: Investigación"]
)

# Simulamos dependecia de usuario para las FK requeridas
def get_current_user_id():
    return 1 # ID de usuario por defecto

# --- INFORME ---
@router.get("/informe", response_model=investigation_schema.InvestigacionInformeResponse, summary="Obtener Informe", description="Obtiene los textos y conclusiones recopilados durante la fase de investigación del proyecto.")
def get_informe(proyecto_id: int, db: Session = Depends(get_db)):
    return investigation_service.get_or_create_informe(db, proyecto_id)

@router.put("/informe", response_model=investigation_schema.InvestigacionInformeResponse, summary="Actualizar Informe", description="Guarda y actualiza los textos detallados del informe como expectativas, situación actual y restricciones.")
def update_informe(proyecto_id: int, informe_data: investigation_schema.InvestigacionInformeCreate, db: Session = Depends(get_db)):
    return investigation_service.update_informe(db, proyecto_id, informe_data)

# --- ARQUETIPOS ---
@router.get("/arquetipos", response_model=List[investigation_schema.ArquetipoUsuarioResponse], summary="Listar Arquetipos", description="Devuelve todos los arquetipos o perfiles de usuario (User Personas) definidos en la investigación.")
def list_arquetipos(proyecto_id: int, db: Session = Depends(get_db)):
    return investigation_service.get_arquetipos(db, proyecto_id)

@router.post("/arquetipos", response_model=investigation_schema.ArquetipoUsuarioResponse, summary="Crear Arquetipo", description="Crea un nuevo arquetipo de usuario junto con su lista inicial de necesidades.")
def create_arquetipo(proyecto_id: int, arquetipo_data: investigation_schema.ArquetipoUsuarioCreate, db: Session = Depends(get_db)):
    return investigation_service.create_arquetipo(db, proyecto_id, arquetipo_data)

@router.put("/arquetipos/{arquetipo_id}", response_model=investigation_schema.ArquetipoUsuarioResponse, summary="Actualizar Arquetipo", description="Edita los datos de un arquetipo específico y sus necesidades.")
def update_arquetipo(proyecto_id: int, arquetipo_id: int, arquetipo_data: investigation_schema.ArquetipoUsuarioUpdate, db: Session = Depends(get_db)):
    return investigation_service.update_arquetipo(db, arquetipo_id, arquetipo_data)

@router.delete("/arquetipos/{arquetipo_id}", summary="Eliminar Arquetipo", description="Elimina un arquetipo del proyecto completamente.")
def delete_arquetipo(proyecto_id: int, arquetipo_id: int, db: Session = Depends(get_db)):
    return investigation_service.delete_arquetipo(db, arquetipo_id)

# --- RECURSOS (ARCHIVOS) ---
@router.post("/recursos", response_model=file_schema.ArchivoResponse, summary="Subir Recurso", description="Permite subir un archivo (imagen, pdf, documento) como recurso de contexto para la Fase 1.")
def upload_recurso(
    proyecto_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    # contexto_tipo para fase 1 recursos
    return file_service.upload_file(
        db=db, 
        file=file, 
        proyecto_id=proyecto_id, 
        subido_por=user_id,
        fase_id=1,
        contexto_tipo="recurso_investigacion"
    )


@router.get("/recursos", response_model=List[file_schema.ArchivoResponse], summary="Listar Recursos", description="Obtiene el listado de todos los archivos físicos subidos a la fase de investigación.")
def get_recursos(proyecto_id: int, db: Session = Depends(get_db)):
    return file_service.get_files_by_phase(db=db, proyecto_id=proyecto_id, fase_id=1)

