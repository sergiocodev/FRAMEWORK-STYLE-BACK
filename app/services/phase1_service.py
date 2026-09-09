from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.phase1_model import InvestigacionInforme, ArquetipoUsuario, ArquetipoNecesidad
from app.schemas.phase1_schema import InvestigacionInformeCreate, ArquetipoUsuarioCreate, ArquetipoUsuarioUpdate

# --- INFORME ---
def get_or_create_informe(db: Session, proyecto_id: int):
    informe = db.query(InvestigacionInforme).filter(InvestigacionInforme.proyecto_id == proyecto_id).first()
    if not informe:
        informe = InvestigacionInforme(proyecto_id=proyecto_id)
        db.add(informe)
        db.commit()
        db.refresh(informe)
    return informe

def update_informe(db: Session, proyecto_id: int, informe_data: InvestigacionInformeCreate):
    informe = get_or_create_informe(db, proyecto_id)
    
    update_data = informe_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(informe, key, value)
        
    db.commit()
    db.refresh(informe)
    return informe

# --- ARQUETIPOS ---
def get_arquetipos(db: Session, proyecto_id: int):
    return db.query(ArquetipoUsuario).filter(ArquetipoUsuario.proyecto_id == proyecto_id).order_by(ArquetipoUsuario.orden).all()

def create_arquetipo(db: Session, proyecto_id: int, arquetipo_data: ArquetipoUsuarioCreate):
    new_arquetipo = ArquetipoUsuario(
        proyecto_id=proyecto_id,
        nombre=arquetipo_data.nombre,
        etiqueta=arquetipo_data.etiqueta,
        orden=arquetipo_data.orden
    )
    db.add(new_arquetipo)
    db.commit()
    db.refresh(new_arquetipo)
    
    if arquetipo_data.necesidades:
        for req in arquetipo_data.necesidades:
            new_req = ArquetipoNecesidad(
                arquetipo_id=new_arquetipo.id,
                descripcion=req.descripcion,
                orden=req.orden
            )
            db.add(new_req)
        db.commit()
        db.refresh(new_arquetipo)
        
    return new_arquetipo

def update_arquetipo(db: Session, arquetipo_id: int, arquetipo_data: ArquetipoUsuarioUpdate):
    arquetipo = db.query(ArquetipoUsuario).filter(ArquetipoUsuario.id == arquetipo_id).first()
    if not arquetipo:
        raise HTTPException(status_code=404, detail="Arquetipo no encontrado")
        
    arquetipo.nombre = arquetipo_data.nombre
    if arquetipo_data.etiqueta is not None:
        arquetipo.etiqueta = arquetipo_data.etiqueta
    if arquetipo_data.orden is not None:
        arquetipo.orden = arquetipo_data.orden
    if arquetipo_data.avatar_archivo_id is not None:
        arquetipo.avatar_archivo_id = arquetipo_data.avatar_archivo_id

    if arquetipo_data.necesidades is not None:
        # Simplest approach: delete old ones and insert new ones
        db.query(ArquetipoNecesidad).filter(ArquetipoNecesidad.arquetipo_id == arquetipo_id).delete()
        for req in arquetipo_data.necesidades:
            new_req = ArquetipoNecesidad(
                arquetipo_id=arquetipo_id,
                descripcion=req.descripcion,
                orden=req.orden
            )
            db.add(new_req)
            
    db.commit()
    db.refresh(arquetipo)
    return arquetipo

def delete_arquetipo(db: Session, arquetipo_id: int):
    arquetipo = db.query(ArquetipoUsuario).filter(ArquetipoUsuario.id == arquetipo_id).first()
    if not arquetipo:
        raise HTTPException(status_code=404, detail="Arquetipo no encontrado")
        
    db.delete(arquetipo)
    db.commit()
    return {"message": "Arquetipo eliminado correctamente"}
