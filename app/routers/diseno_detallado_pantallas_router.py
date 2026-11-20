from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.diseno_conceptual_model import NodoPantalla, TipoNodo, Wireframe
from app.models.diseno_detallado_model import DisenoDetalladoArchivo, DisenoDetalladoChecklistItem
from app.models.file_model import Archivo
from pydantic import BaseModel
from typing import List, Optional
import os

router = APIRouter(prefix="/api/proyectos/{proyecto_id}/fase4-pantallas", tags=["Fase 4: Diseño Detallado"])

class PantallaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = "file"
    prioridad: Optional[str] = "alta"
    wireframe_id: Optional[int] = None

class PantallaUpdate(BaseModel):
    nombre: Optional[str] = None
    prioridad: Optional[str] = None

class PantallaResponse(BaseModel):
    id: int
    proyecto_id: int
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    prioridad: Optional[str] = "media"
    fase_creacion: int
    tiene_wireframe: bool = False
    wireframe_url: Optional[str] = None
    wireframe_id: Optional[int] = None
    wireframe_nombre: Optional[str] = None
    tiene_diseno: bool = False
    diseno_url: Optional[str] = None
    estado_diseno: str = "pendiente" # pendiente, en_revision, verificado
    total_alertas: int = 0
    total_checklists: int = 0
    checklists_aprobados: int = 0

    class Config:
        from_attributes = True

class WireframeDisponibleResponse(BaseModel):
    id: int
    proyecto_id: int
    nombre_archivo: str
    wireframe_url: str
    nodo_id: Optional[int] = None
    nodo_nombre: Optional[str] = None

@router.get("", response_model=List[PantallaResponse], summary="Obtener pantallas de la Fase 4", description="Obtiene todas las pantallas del proyecto con sus prioridades de Fase 2, wireframes y estado de diseño detallado.")
def get_pantallas_fase4(proyecto_id: int, db: Session = Depends(get_db)):
    # Obtener todas las pantallas del proyecto
    nodos = db.query(NodoPantalla).filter(
        NodoPantalla.proyecto_id == proyecto_id,
        NodoPantalla.tipo == TipoNodo.pantalla
    ).all()

    # Prioridad sort: alta (0), media (1), baja (2)
    def priority_sort_key(nodo):
        prio = (nodo.prioridad or "media").lower()
        order = {"alta": 0, "media": 1, "baja": 2}
        return (order.get(prio, 1), nodo.id)

    nodos.sort(key=priority_sort_key)

    # Mapear wireframes
    wireframes = db.query(Wireframe).filter(Wireframe.proyecto_id == proyecto_id).all()
    wf_by_nodo = {w.nodo_id: w for w in wireframes if w.nodo_id}

    # Mapear diseños detallados
    disenos = db.query(DisenoDetalladoArchivo).join(
        NodoPantalla, DisenoDetalladoArchivo.nodo_id == NodoPantalla.id
    ).filter(
        NodoPantalla.proyecto_id == proyecto_id
    ).all()
    diseno_by_nodo = {d.nodo_id: d for d in disenos}

    result = []
    for n in nodos:
        wf = wf_by_nodo.get(n.id)
        wf_url = None
        wf_id = None
        wf_nombre = None
        if wf and wf.archivo:
            wf_url = f"/uploads/wireframes/{os.path.basename(wf.archivo.ruta_almacenamiento)}"
            wf_id = wf.id
            wf_nombre = wf.archivo.nombre_original or f"wireframe_{wf.id}.png"

        diseno = diseno_by_nodo.get(n.id)
        diseno_url = None
        estado = "pendiente"
        alertas_count = 0
        total_chk = 0
        aprob_chk = 0

        if diseno:
            if diseno.archivo:
                diseno_url = f"/uploads/diseno_detallado/{os.path.basename(diseno.archivo.ruta_almacenamiento)}"
            estado = diseno.estado.value if hasattr(diseno.estado, 'value') else str(diseno.estado)
            alertas_count = len(diseno.alertas) if diseno.alertas else 0
            
            # Checklists
            chks = db.query(DisenoDetalladoChecklistItem).filter(DisenoDetalladoChecklistItem.diseno_archivo_id == diseno.id).all()
            total_chk = len(chks)
            aprob_chk = len([c for c in chks if c.estado in ('aprobado', 'aceptado')])

        result.append(PantallaResponse(
            id=n.id,
            proyecto_id=n.proyecto_id,
            nombre=n.nombre,
            descripcion=n.descripcion,
            icono=n.icono or "layout",
            prioridad=n.prioridad or "media",
            fase_creacion=n.fase_creacion,
            tiene_wireframe=bool(wf),
            wireframe_url=wf_url,
            wireframe_id=wf_id,
            wireframe_nombre=wf_nombre,
            tiene_diseno=bool(diseno and diseno.archivo_id),
            diseno_url=diseno_url,
            estado_diseno=estado,
            total_alertas=alertas_count,
            total_checklists=total_chk,
            checklists_aprobados=aprob_chk
        ))

    return result

@router.get("/wireframes-disponibles", response_model=List[WireframeDisponibleResponse], summary="Listar wireframes disponibles de la Fase 2")
def get_wireframes_disponibles(proyecto_id: int, db: Session = Depends(get_db)):
    wireframes = db.query(Wireframe).filter(Wireframe.proyecto_id == proyecto_id).all()
    res = []
    for w in wireframes:
        if w.archivo:
            nodo = db.query(NodoPantalla).filter(NodoPantalla.id == w.nodo_id).first() if w.nodo_id else None
            res.append(WireframeDisponibleResponse(
                id=w.id,
                proyecto_id=w.proyecto_id,
                nombre_archivo=w.archivo.nombre_original or f"wireframe_{w.id}.png",
                wireframe_url=f"/uploads/wireframes/{os.path.basename(w.archivo.ruta_almacenamiento)}",
                nodo_id=w.nodo_id,
                nodo_nombre=nodo.nombre if nodo else None
            ))
    return res

@router.put("/{nodo_id}/vincular-wireframe/{wireframe_id}", summary="Vincular o cambiar wireframe de Fase 2")
def vincular_wireframe(proyecto_id: int, nodo_id: int, wireframe_id: int, db: Session = Depends(get_db)):
    nodo = db.query(NodoPantalla).filter(NodoPantalla.id == nodo_id, NodoPantalla.proyecto_id == proyecto_id).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")
    
    wf = db.query(Wireframe).filter(Wireframe.id == wireframe_id, Wireframe.proyecto_id == proyecto_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Wireframe no encontrado")
        
    # Si este nodo ya tenía otro wireframe vinculado, desvincularlo primero para evitar inconsistencias
    db.query(Wireframe).filter(Wireframe.nodo_id == nodo.id, Wireframe.id != wf.id).update({Wireframe.nodo_id: None})
    
    # Asignar el nuevo wireframe a este nodo
    wf.nodo_id = nodo.id
    db.commit()
    
    wf_url = f"/uploads/wireframes/{os.path.basename(wf.archivo.ruta_almacenamiento)}" if wf.archivo else None
    return {
        "message": f"Wireframe {wireframe_id} vinculado exitosamente a pantalla {nodo.nombre}",
        "nodo_id": nodo.id,
        "wireframe_id": wf.id,
        "wireframe_url": wf_url,
        "nombre_archivo": wf.archivo.nombre_original if wf.archivo else f"wireframe_{wf.id}.png"
    }

@router.delete("/{nodo_id}/desvincular-wireframe", summary="Desvincular wireframe de una pantalla")
def desvincular_wireframe(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    nodo = db.query(NodoPantalla).filter(NodoPantalla.id == nodo_id, NodoPantalla.proyecto_id == proyecto_id).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")
        
    db.query(Wireframe).filter(Wireframe.nodo_id == nodo.id).update({Wireframe.nodo_id: None})
    db.commit()
    return {"message": "Wireframe desvinculado correctamente", "nodo_id": nodo.id}

@router.post("/sincronizar-fase2", response_model=List[PantallaResponse], summary="Sincronizar pantallas y wireframes desde Fase 2")
def sincronizar_fase2(proyecto_id: int, db: Session = Depends(get_db)):
    wireframes = db.query(Wireframe).filter(Wireframe.proyecto_id == proyecto_id).all()
    
    for wf in wireframes:
        nodo_valido = False
        if wf.nodo_id:
            nodo = db.query(NodoPantalla).filter(NodoPantalla.id == wf.nodo_id, NodoPantalla.proyecto_id == proyecto_id).first()
            if nodo:
                nodo_valido = True
        
        if not nodo_valido:
            nombre_sugerido = f"Pantalla {wf.id}"
            icono_sugerido = "layout"
            prioridad_sugerida = "media"
            
            if wf.archivo and wf.archivo.nombre_original:
                nombre_base = os.path.splitext(wf.archivo.nombre_original)[0].lower()
                if "paciente" in nombre_base:
                    nombre_sugerido = "Pacientes"
                    icono_sugerido = "user"
                    prioridad_sugerida = "alta"
                elif "catalog" in nombre_base:
                    nombre_sugerido = "Catálogo"
                    icono_sugerido = "layout"
                    prioridad_sugerida = "alta"
                elif "login" in nombre_base or "captura" in nombre_base:
                    nombre_sugerido = "Login / Acceso"
                    icono_sugerido = "log-in"
                    prioridad_sugerida = "media"
                elif "agenda" in nombre_base:
                    nombre_sugerido = "Agenda"
                    icono_sugerido = "folder"
                    prioridad_sugerida = "alta"
                else:
                    nombre_sugerido = wf.archivo.nombre_original.split('.')[0].strip()[:25]
                    
            nuevo_nodo = NodoPantalla(
                proyecto_id=proyecto_id,
                nombre=nombre_sugerido,
                prioridad=prioridad_sugerida,
                tipo=TipoNodo.pantalla,
                icono=icono_sugerido,
                fase_creacion=2
            )
            db.add(nuevo_nodo)
            db.commit()
            db.refresh(nuevo_nodo)
            
            wf.nodo_id = nuevo_nodo.id
            db.commit()
            
    return get_pantallas_fase4(proyecto_id, db)

@router.post("", response_model=PantallaResponse, summary="Crear nueva pantalla en la Fase 4", description="Crea una nueva pantalla asociada al proyecto para diseño detallado.")
def create_pantalla_fase4(proyecto_id: int, pantalla: PantallaCreate, db: Session = Depends(get_db)):
    nuevo_nodo = NodoPantalla(
        proyecto_id=proyecto_id,
        nombre=pantalla.nombre,
        descripcion=pantalla.descripcion,
        icono=pantalla.icono,
        prioridad=pantalla.prioridad or "alta",
        tipo=TipoNodo.pantalla,
        fase_creacion=4
    )
    db.add(nuevo_nodo)
    db.commit()
    db.refresh(nuevo_nodo)

    wf_url = None
    wf_id = None
    wf_nombre = None
    if pantalla.wireframe_id:
        wf = db.query(Wireframe).filter(Wireframe.id == pantalla.wireframe_id, Wireframe.proyecto_id == proyecto_id).first()
        if wf:
            wf.nodo_id = nuevo_nodo.id
            db.commit()
            wf_id = wf.id
            if wf.archivo:
                wf_url = f"/uploads/wireframes/{os.path.basename(wf.archivo.ruta_almacenamiento)}"
                wf_nombre = wf.archivo.nombre_original

    return PantallaResponse(
        id=nuevo_nodo.id,
        proyecto_id=nuevo_nodo.proyecto_id,
        nombre=nuevo_nodo.nombre,
        descripcion=nuevo_nodo.descripcion,
        icono=nuevo_nodo.icono,
        prioridad=nuevo_nodo.prioridad,
        fase_creacion=nuevo_nodo.fase_creacion,
        tiene_wireframe=bool(wf_url),
        wireframe_url=wf_url,
        wireframe_id=wf_id,
        wireframe_nombre=wf_nombre,
        tiene_diseno=False,
        diseno_url=None,
        estado_diseno="pendiente"
    )

@router.put("/{nodo_id}", response_model=PantallaResponse, summary="Actualizar pantalla de la Fase 4")
def update_pantalla_fase4(proyecto_id: int, nodo_id: int, pantalla: PantallaUpdate, db: Session = Depends(get_db)):
    nodo = db.query(NodoPantalla).filter(
        NodoPantalla.id == nodo_id, 
        NodoPantalla.proyecto_id == proyecto_id
    ).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")
    if pantalla.nombre is not None:
        nodo.nombre = pantalla.nombre
    if pantalla.prioridad is not None:
        nodo.prioridad = pantalla.prioridad
    db.commit()
    db.refresh(nodo)
    
    wf = db.query(Wireframe).filter(Wireframe.nodo_id == nodo_id).first()
    wf_url = f"/uploads/wireframes/{os.path.basename(wf.archivo.ruta_almacenamiento)}" if wf and wf.archivo else None
    wf_id = wf.id if wf else None
    wf_nombre = wf.archivo.nombre_original if wf and wf.archivo else None
    
    diseno = db.query(DisenoDetalladoArchivo).filter(DisenoDetalladoArchivo.nodo_id == nodo_id).first()
    diseno_url = f"/uploads/diseno_detallado/{os.path.basename(diseno.archivo.ruta_almacenamiento)}" if diseno and diseno.archivo else None
    estado = (diseno.estado.value if hasattr(diseno.estado, 'value') else str(diseno.estado)) if diseno else "pendiente"

    return PantallaResponse(
        id=nodo.id,
        proyecto_id=nodo.proyecto_id,
        nombre=nodo.nombre,
        descripcion=nodo.descripcion,
        icono=nodo.icono,
        prioridad=nodo.prioridad,
        fase_creacion=nodo.fase_creacion,
        tiene_wireframe=bool(wf),
        wireframe_url=wf_url,
        wireframe_id=wf_id,
        wireframe_nombre=wf_nombre,
        tiene_diseno=bool(diseno and diseno.archivo_id),
        diseno_url=diseno_url,
        estado_diseno=estado
    )

@router.delete("/{nodo_id}", summary="Eliminar pantalla de la Fase 4")
def delete_pantalla_fase4(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    nodo = db.query(NodoPantalla).filter(
        NodoPantalla.id == nodo_id, 
        NodoPantalla.proyecto_id == proyecto_id
    ).first()
    if not nodo:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")
    db.delete(nodo)
    db.commit()
    return {"message": "Pantalla eliminada correctamente"}
