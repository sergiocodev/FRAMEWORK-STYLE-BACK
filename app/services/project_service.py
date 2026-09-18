from sqlalchemy.orm import Session
from app.models.project_model import Proyecto
from app.schemas.project_schema import ProyectoCreate, ProyectoUpdate
from fastapi import HTTPException

def get_projects(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Proyecto).filter(Proyecto.user_id == user_id).offset(skip).limit(limit).all()

def get_project_by_id(db: Session, project_id: int, user_id: int):
    project = db.query(Proyecto).filter(Proyecto.id == project_id, Proyecto.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

def create_project(db: Session, project_in: ProyectoCreate, user_id: int):
    # Asignamos el user_id autenticado al nuevo proyecto
    new_project_data = project_in.model_dump()
    new_project_data["user_id"] = user_id
    new_project = Proyecto(**new_project_data)
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

def update_project(db: Session, project_id: int, project_in: ProyectoUpdate, user_id: int):
    # Validamos pertenencia
    project = get_project_by_id(db, project_id, user_id)
    update_data = project_in.model_dump(exclude_unset=True)
    
    # Prevenimos que se cambie el responsable por error o de manera maliciosa
    if "user_id" in update_data:
        del update_data["user_id"]
        
    for key, value in update_data.items():
        setattr(project, key, value)
        
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def delete_project(db: Session, project_id: int, user_id: int):
    # Validamos pertenencia
    project = get_project_by_id(db, project_id, user_id)
    db.delete(project)
    db.commit()
    return {"message": "Proyecto eliminado exitosamente"}
