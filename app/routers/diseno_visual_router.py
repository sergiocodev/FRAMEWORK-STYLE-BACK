from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas import diseno_visual_schema as schemas
from app.services import diseno_visual_service as service

router = APIRouter(
    prefix="/api/diseno-visual",
    tags=["Diseno Visual"]
)

@router.get("/{proyecto_id}/completo", response_model=schemas.DisenoVisualCompletoResponse)
def get_diseno_visual_completo(proyecto_id: int, db: Session = Depends(get_db)):
    config = service.get_config(db, proyecto_id)
    colores = service.get_colores(db, proyecto_id)
    tipografias = service.get_tipografias(db, proyecto_id)
    iconos = service.get_iconos(db, proyecto_id)
    
    # Si no hay config, retornamos null pero con arrays vacíos de colores y tipografías
    return {
        "config": config,
        "colores": colores or [],
        "tipografias": tipografias or [],
        "iconos": iconos or []
    }

@router.put("/config", response_model=schemas.DisenoVisualConfigResponse)
def update_config(config_in: schemas.DisenoVisualConfigCreate, db: Session = Depends(get_db)):
    return service.upsert_config(db, config_in)

@router.post("/colores", response_model=schemas.ColorItemResponse)
def add_color(color_in: schemas.ColorItemCreate, db: Session = Depends(get_db)):
    return service.add_color(db, color_in)

@router.put("/colores/{color_id}", response_model=schemas.ColorItemResponse)
def update_color(color_id: int, color_in: schemas.ColorItemUpdate, db: Session = Depends(get_db)):
    color = service.update_color(db, color_id, color_in)
    if not color:
        raise HTTPException(status_code=404, detail="Color not found")
    return color

@router.delete("/colores/{color_id}")
def delete_color(color_id: int, db: Session = Depends(get_db)):
    color = service.delete_color(db, color_id)
    if not color:
        raise HTTPException(status_code=404, detail="Color not found")
    return {"message": "Color deleted"}

@router.post("/tipografias", response_model=schemas.TypographyItemResponse)
def add_tipografia(tipo_in: schemas.TypographyItemCreate, db: Session = Depends(get_db)):
    return service.add_tipografia(db, tipo_in)

@router.put("/tipografias/{tipo_id}", response_model=schemas.TypographyItemResponse)
def update_tipografia(tipo_id: int, tipo_in: schemas.TypographyItemUpdate, db: Session = Depends(get_db)):
    tipo = service.update_tipografia(db, tipo_id, tipo_in)
    if not tipo:
        raise HTTPException(status_code=404, detail="Typography not found")
    return tipo

@router.delete("/tipografias/{tipo_id}")
def delete_tipografia(tipo_id: int, db: Session = Depends(get_db)):
    tipo = service.delete_tipografia(db, tipo_id)
    if not tipo:
        raise HTTPException(status_code=404, detail="Typography not found")
    return {"message": "Typography deleted"}

@router.post("/iconos", response_model=schemas.IconItemResponse)
def add_icono(icon_in: schemas.IconItemCreate, db: Session = Depends(get_db)):
    return service.add_icono(db, icon_in)

@router.delete("/iconos/{icon_id}")
def delete_icono(icon_id: int, db: Session = Depends(get_db)):
    icon = service.delete_icono(db, icon_id)
    if not icon:
        raise HTTPException(status_code=404, detail="Icon not found")
    return {"message": "Icon deleted"}
