from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.diseno_conceptual_model import NodoPantalla, TipoNodo, Wireframe
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/api/proyectos/{proyecto_id}/fase4-pantallas", tags=["Fase 4: Diseño Detallado"])

class PantallaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = "file"

class PantallaUpdate(BaseModel):
    nombre: str

class PantallaResponse(BaseModel):
    id: int
    proyecto_id: int
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    fase_creacion: int

    class Config:
        from_attributes = True

@router.get("", response_model=List[PantallaResponse], summary="Obtener pantallas de la Fase 4", description="Obtiene todas las pantallas creadas en la Fase 4 para el proyecto especificado. Si no existen, realiza una copia inteligente de los wireframes previamente cargados.")
def get_pantallas_fase4(proyecto_id: int, db: Session = Depends(get_db)):
    nodos_fase4 = db.query(NodoPantalla).filter(
        NodoPantalla.proyecto_id == proyecto_id,
        NodoPantalla.tipo == TipoNodo.pantalla,
        NodoPantalla.fase_creacion == 4
    ).all()
    
    if not nodos_fase4:
        # Copia inteligente: buscar en la tabla Wireframes
        wireframes = db.query(Wireframe).filter(Wireframe.proyecto_id == proyecto_id).all()
        
        for w in wireframes:
            # Usar titulo si existe, sino un fallback
            nombre_wf = w.titulo if w.titulo else f"Wireframe {w.id}"
            
            nuevo_nodo = NodoPantalla(
                proyecto_id=proyecto_id,
                nombre=nombre_wf,
                descripcion="Importado desde wireframes",
                icono="image",
                tipo=TipoNodo.pantalla,
                fase_creacion=4
            )
            db.add(nuevo_nodo)
            nodos_fase4.append(nuevo_nodo)
            
        if nodos_fase4:
            db.commit()
            for n in nodos_fase4:
                db.refresh(n)

    return nodos_fase4

@router.post("", response_model=PantallaResponse, summary="Crear nueva pantalla en la Fase 4", description="Crea una nueva pantalla independiente que solo existirá en el diseño detallado (Fase 4), sin afectar la estructura base.")
def create_pantalla_fase4(proyecto_id: int, pantalla: PantallaCreate, db: Session = Depends(get_db)):
    nuevo_nodo = NodoPantalla(
        proyecto_id=proyecto_id,
        nombre=pantalla.nombre,
        descripcion=pantalla.descripcion,
        icono=pantalla.icono,
        tipo=TipoNodo.pantalla,
        fase_creacion=4
    )
    db.add(nuevo_nodo)
    db.commit()
    db.refresh(nuevo_nodo)
    return nuevo_nodo

@router.put("/{nodo_id}", response_model=PantallaResponse, summary="Actualizar pantalla de la Fase 4", description="Actualiza el nombre de una pantalla.")
def update_pantalla_fase4(proyecto_id: int, nodo_id: int, pantalla: PantallaUpdate, db: Session = Depends(get_db)):
    nodo = db.query(NodoPantalla).filter(
        NodoPantalla.id == nodo_id, 
        NodoPantalla.proyecto_id == proyecto_id,
        NodoPantalla.fase_creacion == 4
    ).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada en la Fase 4")
    nodo.nombre = pantalla.nombre
    db.commit()
    db.refresh(nodo)
    return nodo

@router.delete("/{nodo_id}", summary="Eliminar pantalla de la Fase 4", description="Elimina permanentemente una pantalla del diseño detallado. Esta acción no eliminará el wireframe o nodo original del que pudo ser importada.")
def delete_pantalla_fase4(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    nodo = db.query(NodoPantalla).filter(
        NodoPantalla.id == nodo_id, 
        NodoPantalla.proyecto_id == proyecto_id,
        NodoPantalla.fase_creacion == 4
    ).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada en la Fase 4")
    db.delete(nodo)
    db.commit()
    return {"message": "Pantalla eliminada correctamente"}
