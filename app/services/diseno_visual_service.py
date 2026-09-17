from sqlalchemy.orm import Session
from app.models.diseno_visual_model import DisenoVisualConfig, ColorItem, TypographyItem, IconItem
from app.schemas.diseno_visual_schema import (
    DisenoVisualConfigCreate, 
    ColorItemCreate, 
    ColorItemUpdate, 
    TypographyItemCreate, 
    TypographyItemUpdate,
    IconItemCreate,
    IconItemUpdate
)

def get_config(db: Session, proyecto_id: int):
    return db.query(DisenoVisualConfig).filter(DisenoVisualConfig.proyecto_id == proyecto_id).first()

def upsert_config(db: Session, config_in: DisenoVisualConfigCreate):
    config = get_config(db, config_in.proyecto_id)
    if not config:
        config = DisenoVisualConfig(**config_in.dict())
        db.add(config)
    else:
        for var, value in config_in.dict(exclude_unset=True).items():
            setattr(config, var, value)
    db.commit()
    db.refresh(config)
    return config

def get_colores(db: Session, proyecto_id: int):
    return db.query(ColorItem).filter(ColorItem.proyecto_id == proyecto_id).order_by(ColorItem.orden).all()

def add_color(db: Session, color_in: ColorItemCreate):
    color = ColorItem(**color_in.dict())
    db.add(color)
    db.commit()
    db.refresh(color)
    return color

def update_color(db: Session, color_id: int, color_in: ColorItemUpdate):
    color = db.query(ColorItem).filter(ColorItem.id == color_id).first()
    if color:
        for var, value in color_in.dict(exclude_unset=True).items():
            setattr(color, var, value)
        db.commit()
        db.refresh(color)
    return color

def delete_color(db: Session, color_id: int):
    color = db.query(ColorItem).filter(ColorItem.id == color_id).first()
    if color:
        db.delete(color)
        db.commit()
    return color

def get_tipografias(db: Session, proyecto_id: int):
    return db.query(TypographyItem).filter(TypographyItem.proyecto_id == proyecto_id).order_by(TypographyItem.orden).all()

def add_tipografia(db: Session, tipo_in: TypographyItemCreate):
    tipo = TypographyItem(**tipo_in.dict())
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo

def update_tipografia(db: Session, tipo_id: int, tipo_in: TypographyItemUpdate):
    tipo = db.query(TypographyItem).filter(TypographyItem.id == tipo_id).first()
    if tipo:
        for var, value in tipo_in.dict(exclude_unset=True).items():
            setattr(tipo, var, value)
        db.commit()
        db.refresh(tipo)
    return tipo

def delete_tipografia(db: Session, tipo_id: int):
    tipo = db.query(TypographyItem).filter(TypographyItem.id == tipo_id).first()
    if tipo:
        db.delete(tipo)
        db.commit()
    return tipo

from typing import List

def replace_tipografias(db: Session, proyecto_id: int, tipografias_in: List[TypographyItemCreate]):
    # Borrar existentes de forma atómica
    db.query(TypographyItem).filter(TypographyItem.proyecto_id == proyecto_id).delete()
    
    # Crear nuevos
    nuevas = []
    for tipo_in in tipografias_in:
        # Asegurarnos de que el proyecto_id es el correcto
        tipo_data = tipo_in.dict()
        tipo_data["proyecto_id"] = proyecto_id
        nuevo_tipo = TypographyItem(**tipo_data)
        db.add(nuevo_tipo)
        nuevas.append(nuevo_tipo)
        
    db.commit()
    
    # Refrescar para obtener los IDs autogenerados
    for tipo in nuevas:
        db.refresh(tipo)
        
    return nuevas

def get_iconos(db: Session, proyecto_id: int):
    return db.query(IconItem).filter(IconItem.proyecto_id == proyecto_id).all()

def add_icono(db: Session, icon_in: IconItemCreate):
    icon = IconItem(**icon_in.dict())
    db.add(icon)
    db.commit()
    db.refresh(icon)
    return icon

def delete_icono(db: Session, icon_id: int):
    icon = db.query(IconItem).filter(IconItem.id == icon_id).first()
    if icon:
        db.delete(icon)
        db.commit()
    return icon
