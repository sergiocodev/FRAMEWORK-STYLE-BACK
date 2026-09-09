from sqlalchemy.orm import Session
from app.models.project_model import Proyecto
from app.schemas.project_schema import ProyectoCreate, ProyectoUpdate
from fastapi import HTTPException

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Proyecto).offset(skip).limit(limit).all()

def get_project_by_id(db: Session, project_id: int):
    project = db.query(Proyecto).filter(Proyecto.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

def create_project(db: Session, project_in: ProyectoCreate):
    new_project = Proyecto(**project_in.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

def update_project(db: Session, project_id: int, project_in: ProyectoUpdate):
    project = get_project_by_id(db, project_id)
    update_data = project_in.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(project, key, value)
        
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def delete_project(db: Session, project_id: int):
    project = get_project_by_id(db, project_id)
    db.delete(project)
    db.commit()
    return {"message": "Proyecto eliminado exitosamente"}
