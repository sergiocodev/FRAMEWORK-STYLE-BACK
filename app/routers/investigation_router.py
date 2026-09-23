from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user

from app.schemas import investigation_schema, file_schema, user_schema
from app.services import investigation_service, file_service, project_service

router = APIRouter(
    prefix="/api/v1/proyectos/{proyecto_id}/investigation",
    tags=["Fase 1: Investigación"]
)

def verify_project_ownership(db: Session, proyecto_id: int, user_id: int):
    # This will throw 404 if the user doesn't own the project or if it doesn't exist.
    return project_service.get_project_by_id(db, proyecto_id, user_id)

# --- INFORME ---
@router.get("/informe", response_model=investigation_schema.InvestigacionInformeResponse, summary="Obtener Informe", description="Obtiene los textos y conclusiones recopilados durante la fase de investigación del proyecto.")
def get_informe(proyecto_id: int, db: Session = Depends(get_db), current_user: user_schema.User = Depends(get_current_user)):
    verify_project_ownership(db, proyecto_id, current_user.id)
    return investigation_service.get_or_create_informe(db, proyecto_id)

@router.put("/informe", response_model=investigation_schema.InvestigacionInformeResponse, summary="Actualizar Informe", description="Guarda y actualiza los textos detallados del informe como expectativas, situación actual y restricciones.")
def update_informe(proyecto_id: int, informe_data: investigation_schema.InvestigacionInformeCreate, db: Session = Depends(get_db), current_user: user_schema.User = Depends(get_current_user)):
    verify_project_ownership(db, proyecto_id, current_user.id)
    return investigation_service.update_informe(db, proyecto_id, informe_data)

# --- ARQUETIPOS ---
@router.get("/arquetipos", response_model=List[investigation_schema.ArquetipoUsuarioResponse], summary="Listar Arquetipos", description="Devuelve todos los arquetipos o perfiles de usuario (User Personas) definidos en la investigación.")
def list_arquetipos(proyecto_id: int, db: Session = Depends(get_db), current_user: user_schema.User = Depends(get_current_user)):
    verify_project_ownership(db, proyecto_id, current_user.id)
    return investigation_service.get_arquetipos(db, proyecto_id)

@router.post("/arquetipos", response_model=investigation_schema.ArquetipoUsuarioResponse, summary="Crear Arquetipo", description="Crea un nuevo arquetipo de usuario junto con su lista inicial de necesidades.")
def create_arquetipo(proyecto_id: int, arquetipo_data: investigation_schema.ArquetipoUsuarioCreate, db: Session = Depends(get_db), current_user: user_schema.User = Depends(get_current_user)):
    verify_project_ownership(db, proyecto_id, current_user.id)
    return investigation_service.create_arquetipo(db, proyecto_id, arquetipo_data)

@router.put("/arquetipos/{arquetipo_id}", response_model=investigation_schema.ArquetipoUsuarioResponse, summary="Actualizar Arquetipo", description="Edita los datos de un arquetipo específico y sus necesidades.")
def update_arquetipo(proyecto_id: int, arquetipo_id: int, arquetipo_data: investigation_schema.ArquetipoUsuarioUpdate, db: Session = Depends(get_db), current_user: user_schema.User = Depends(get_current_user)):
    verify_project_ownership(db, proyecto_id, current_user.id)
    return investigation_service.update_arquetipo(db, arquetipo_id, arquetipo_data)

@router.delete("/arquetipos/{arquetipo_id}", summary="Eliminar Arquetipo", description="Elimina un arquetipo del proyecto completamente.")
def delete_arquetipo(proyecto_id: int, arquetipo_id: int, db: Session = Depends(get_db), current_user: user_schema.User = Depends(get_current_user)):
    verify_project_ownership(db, proyecto_id, current_user.id)
    return investigation_service.delete_arquetipo(db, arquetipo_id)

# --- RECURSOS (ARCHIVOS) ---
@router.post("/recursos", response_model=file_schema.ArchivoResponse, summary="Subir Recurso", description="Permite subir un archivo (imagen, pdf, documento) como recurso de contexto para la Fase 1.")
def upload_recurso(
    proyecto_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    verify_project_ownership(db, proyecto_id, current_user.id)
    # contexto_tipo para fase 1 recursos
    return file_service.upload_file(
        db=db, 
        file=file, 
        proyecto_id=proyecto_id, 
        subido_por=current_user.id,
        fase_id=1,
        contexto_tipo="recurso_investigacion"
    )


@router.get("/recursos", response_model=List[file_schema.ArchivoResponse], summary="Listar Recursos", description="Obtiene el listado de todos los archivos físicos subidos a la fase de investigación.")
def get_recursos(proyecto_id: int, db: Session = Depends(get_db), current_user: user_schema.User = Depends(get_current_user)):
    verify_project_ownership(db, proyecto_id, current_user.id)
    return file_service.get_files_by_phase(db=db, proyecto_id=proyecto_id, fase_id=1, contexto_tipo="recurso_investigacion")

@router.delete("/recursos/{archivo_id}", summary="Eliminar Recurso", description="Elimina un recurso subido en la fase de investigación.")
def delete_recurso(
    proyecto_id: int, 
    archivo_id: int, 
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    verify_project_ownership(db, proyecto_id, current_user.id)
    from app.models import file_model
    import os
    
    archivo = db.query(file_model.Archivo).filter(
        file_model.Archivo.id == archivo_id,
        file_model.Archivo.proyecto_id == proyecto_id
    ).first()
    
    if not archivo:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
    if os.path.exists(archivo.ruta_almacenamiento):
        os.remove(archivo.ruta_almacenamiento)
        
    db.delete(archivo)
    db.commit()
    return {"message": "Archivo eliminado correctamente"}

@router.post("/referencias/upload", summary="Subir Referencia (Imagen)", description="Sube una imagen para la sección de expectativas/referencias y devuelve su URL.")
def upload_referencia(
    proyecto_id: int, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: user_schema.User = Depends(get_current_user)
):
    verify_project_ownership(db, proyecto_id, current_user.id)
    archivo = file_service.upload_file(
        db=db, 
        file=file, 
        proyecto_id=proyecto_id, 
        subido_por=current_user.id,
        fase_id=1,
        contexto_tipo="referencia_investigacion"
    )
    url_path = "/" + archivo.ruta_almacenamiento.replace("\\", "/")
    # environment variable for backend URL is commonly used, but since we are running locally with CORS, 
    # returning the absolute path relative to the domain is enough: "/uploads/uuid.png" 
    # but since the frontend expects full URL or uses environment apiUrl, it's safer to just return the path
    # and the frontend will prepend the apiUrl. Actually, the frontend image tag just uses src="http://localhost:8000/uploads/..." 
    # Let's check environment.apiUrl in frontend. For now, returning full path or relative path depends on frontend.
    # We will return the relative path and let the frontend format it if necessary.
    return {"url": url_path}
