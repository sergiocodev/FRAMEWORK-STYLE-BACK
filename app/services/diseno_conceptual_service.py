from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.diseno_conceptual_model import NodoPantalla, NodoConexion, ContenidoItem, Wireframe, WireframeChecklistItem
from app.schemas.diseno_conceptual_schema import (
    NodoPantallaCreate, NodoPantallaUpdate, NodoConexionCreate,
    ContenidoItemCreate, WireframeCreate
)

# --- NODOS (PANTALLAS) ---
def get_nodos(db: Session, proyecto_id: int):
    return db.query(NodoPantalla).filter(NodoPantalla.proyecto_id == proyecto_id).all()

def create_nodo(db: Session, proyecto_id: int, nodo_data: NodoPantallaCreate):
    new_nodo = NodoPantalla(
        proyecto_id=proyecto_id,
        nombre=nodo_data.nombre,
        tipo=nodo_data.tipo,
        icono=nodo_data.icono,
        descripcion=nodo_data.descripcion,
        pos_x=nodo_data.pos_x,
        pos_y=nodo_data.pos_y,
        estado_verificacion=nodo_data.estado_verificacion,
        enlace_diseno_externo=nodo_data.enlace_diseno_externo
    )
    db.add(new_nodo)
    db.commit()
    db.refresh(new_nodo)
    
    if nodo_data.contenidos:
        for cont in nodo_data.contenidos:
            new_cont = ContenidoItem(
                proyecto_id=proyecto_id,
                nodo_id=new_nodo.id,
                tipo=cont.tipo,
                nombre=cont.nombre,
                detalle=cont.detalle,
                prioridad=cont.prioridad,
                archivo_id=cont.archivo_id,
                orden=cont.orden
            )
            db.add(new_cont)
        db.commit()
        db.refresh(new_nodo)
        
    return new_nodo

def update_nodo(db: Session, nodo_id: int, nodo_data: NodoPantallaUpdate):
    nodo = db.query(NodoPantalla).filter(NodoPantalla.id == nodo_id).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
    update_data = nodo_data.model_dump(exclude_unset=True, exclude={"contenidos"})
    for key, value in update_data.items():
        setattr(nodo, key, value)
        
    if nodo_data.contenidos is not None:
        db.query(ContenidoItem).filter(ContenidoItem.nodo_id == nodo_id).delete()
        for cont in nodo_data.contenidos:
            new_cont = ContenidoItem(
                proyecto_id=nodo.proyecto_id,
                nodo_id=nodo.id,
                tipo=cont.tipo,
                nombre=cont.nombre,
                detalle=cont.detalle,
                prioridad=cont.prioridad,
                archivo_id=cont.archivo_id,
                orden=cont.orden
            )
            db.add(new_cont)
            
    db.commit()
    db.refresh(nodo)
    return nodo

def delete_nodo(db: Session, nodo_id: int):
    nodo = db.query(NodoPantalla).filter(NodoPantalla.id == nodo_id).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
    db.delete(nodo)
    db.commit()
    return {"message": "Nodo eliminado correctamente"}

# --- CONEXIONES ---
def get_conexiones(db: Session, proyecto_id: int):
    return db.query(NodoConexion).filter(NodoConexion.proyecto_id == proyecto_id).all()

def create_conexion(db: Session, proyecto_id: int, conexion_data: NodoConexionCreate):
    new_conexion = NodoConexion(
        proyecto_id=proyecto_id,
        nodo_origen_id=conexion_data.nodo_origen_id,
        nodo_destino_id=conexion_data.nodo_destino_id,
        tipo_conexion=conexion_data.tipo_conexion
    )
    db.add(new_conexion)
    db.commit()
    db.refresh(new_conexion)
    return new_conexion

def delete_conexion(db: Session, conexion_id: int):
    conexion = db.query(NodoConexion).filter(NodoConexion.id == conexion_id).first()
    if not conexion:
        raise HTTPException(status_code=404, detail="Conexion no encontrada")
    db.delete(conexion)
    db.commit()
    return {"message": "Conexion eliminada correctamente"}

# --- INVENTARIO GLOBAL ---
def get_inventario(db: Session, proyecto_id: int):
    return db.query(ContenidoItem).filter(
        ContenidoItem.proyecto_id == proyecto_id, 
        ContenidoItem.nodo_id == None
    ).all()

def create_contenido_inventario(db: Session, proyecto_id: int, contenido_data: ContenidoItemCreate):
    new_cont = ContenidoItem(
        proyecto_id=proyecto_id,
        nodo_id=None,
        tipo=contenido_data.tipo,
        nombre=contenido_data.nombre,
        detalle=contenido_data.detalle,
        prioridad=contenido_data.prioridad,
        archivo_id=contenido_data.archivo_id,
        orden=contenido_data.orden
    )
    db.add(new_cont)
    db.commit()
    db.refresh(new_cont)
    return new_cont

# --- WIREFRAMES ---
def get_wireframes(db: Session, proyecto_id: int):
    return db.query(Wireframe).filter(Wireframe.proyecto_id == proyecto_id).all()

def create_wireframe(db: Session, proyecto_id: int, wireframe_data: WireframeCreate):
    new_wireframe = Wireframe(
        proyecto_id=proyecto_id,
        nodo_id=wireframe_data.nodo_id,
        archivo_id=wireframe_data.archivo_id,
        version=wireframe_data.version,
        generado_por_ia=wireframe_data.generado_por_ia
    )
    db.add(new_wireframe)
    db.commit()
    db.refresh(new_wireframe)
    return new_wireframe


# --- INVENTARIO ADICIONAL ---
from app.schemas.diseno_conceptual_schema import ContenidoItemUpdate

def update_contenido_inventario(db: Session, item_id: int, item_data: ContenidoItemUpdate):
    item = db.query(ContenidoItem).filter(ContenidoItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
    
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item

def delete_contenido_inventario(db: Session, item_id: int):
    item = db.query(ContenidoItem).filter(ContenidoItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
    db.delete(item)
    db.commit()
    return {"message": "Item de inventario eliminado"}

# --- WIREFRAMES ADICIONAL ---
def delete_wireframe(db: Session, wireframe_id: int):
    wireframe = db.query(Wireframe).filter(Wireframe.id == wireframe_id).first()
    if not wireframe:
        raise HTTPException(status_code=404, detail="Wireframe no encontrado")
    db.delete(wireframe)
    db.commit()
    return {"message": "Wireframe eliminado correctamente"}

# --- PHASE 2 CHECKLIST ---
from app.models.diseno_conceptual_model import DisenoConceptualChecklistItem
from app.schemas.diseno_conceptual_schema import (
    DisenoConceptualChecklistItemCreate, DisenoConceptualChecklistItemUpdate, WireframeChecklistItemUpdate, WireframeChecklistItemCreate
)

def get_project_checklist(db: Session, proyecto_id: int):
    return db.query(DisenoConceptualChecklistItem).filter(DisenoConceptualChecklistItem.proyecto_id == proyecto_id).all()

def create_project_checklist_item(db: Session, proyecto_id: int, item_data: DisenoConceptualChecklistItemCreate):
    new_item = DisenoConceptualChecklistItem(
        proyecto_id=proyecto_id,
        pregunta=item_data.pregunta,
        origen=item_data.origen,
        estado=item_data.estado
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

def update_project_checklist_item(db: Session, item_id: int, item_data: DisenoConceptualChecklistItemUpdate):
    item = db.query(DisenoConceptualChecklistItem).filter(DisenoConceptualChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
        
    db.commit()
    db.refresh(item)
    return item

def delete_project_checklist_item(db: Session, item_id: int):
    item = db.query(DisenoConceptualChecklistItem).filter(DisenoConceptualChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    db.delete(item)
    db.commit()
    return {"message": "Item eliminado"}

# --- WIREFRAME CHECKLIST ---
def get_wireframe_checklist(db: Session, wireframe_id: int):
    return db.query(WireframeChecklistItem).filter(WireframeChecklistItem.wireframe_id == wireframe_id).all()

def create_wireframe_checklist_item(db: Session, wireframe_id: int, item_data: WireframeChecklistItemCreate):
    new_item = WireframeChecklistItem(
        wireframe_id=wireframe_id,
        pregunta=item_data.pregunta,
        origen=item_data.origen,
        estado=item_data.estado
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

def update_wireframe_checklist_item(db: Session, item_id: int, item_data: WireframeChecklistItemUpdate):
    item = db.query(WireframeChecklistItem).filter(WireframeChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
        
    db.commit()
    db.refresh(item)
    return item

def delete_wireframe_checklist_item(db: Session, item_id: int):
    item = db.query(WireframeChecklistItem).filter(WireframeChecklistItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    db.delete(item)
    db.commit()
    return {"message": "Item eliminado"}
