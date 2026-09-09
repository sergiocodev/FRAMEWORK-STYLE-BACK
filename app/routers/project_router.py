from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas import project_schema
from app.services import project_service

router = APIRouter(
    prefix="/api/v1/proyectos",
    tags=["Proyectos"]
)

@router.get("", response_model=List[project_schema.ProyectoResponse])
def list_proyectos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return project_service.get_projects(db, skip=skip, limit=limit)

@router.post("", response_model=project_schema.ProyectoResponse, status_code=status.HTTP_201_CREATED)
def create_proyecto(project_in: project_schema.ProyectoCreate, db: Session = Depends(get_db)):
    return project_service.create_project(db, project_in)

@router.get("/{proyecto_id}", response_model=project_schema.ProyectoResponse)
def get_proyecto(proyecto_id: int, db: Session = Depends(get_db)):
    return project_service.get_project_by_id(db, proyecto_id)

@router.put("/{proyecto_id}", response_model=project_schema.ProyectoResponse)
def update_proyecto(proyecto_id: int, project_in: project_schema.ProyectoUpdate, db: Session = Depends(get_db)):
    return project_service.update_project(db, proyecto_id, project_in)

@router.delete("/{proyecto_id}", status_code=status.HTTP_200_OK)
def delete_proyecto(proyecto_id: int, db: Session = Depends(get_db)):
    return project_service.delete_project(db, proyecto_id)
