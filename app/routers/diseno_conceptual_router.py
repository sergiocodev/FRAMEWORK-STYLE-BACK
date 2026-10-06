from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas import diseno_conceptual_schema
from app.services import diseno_conceptual_service

router = APIRouter(
    prefix="/api/v1/proyectos/{proyecto_id}/diseno_conceptual",
    tags=["Fase 2: Diseño Conceptual"]
)

# --- NODOS ---
@router.get("/nodos", response_model=List[diseno_conceptual_schema.NodoPantallaResponse], summary="Listar todos los Nodos (Pantallas) del Mapa Conceptual", description="Devuelve una lista de todos los nodos (pantallas o componentes) creados en el canvas, junto con sus contenidos anidados.")
def get_nodos(proyecto_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.get_nodos(db, proyecto_id)

@router.post("/nodos", response_model=diseno_conceptual_schema.NodoPantallaResponse, summary="Crear un nuevo Nodo (Pantalla/Caja) en el Canvas", description="Crea una nueva caja o pantalla en el canvas del proyecto. Puedes enviar coordenadas iniciales y una lista de contenidos hijos.")
def create_nodo(proyecto_id: int, nodo_data: diseno_conceptual_schema.NodoPantallaCreate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.create_nodo(db, proyecto_id, nodo_data)

@router.put("/nodos/{nodo_id}", response_model=diseno_conceptual_schema.NodoPantallaResponse, summary="Modificar propiedades o posición de un Nodo", description="Modifica las propiedades de un nodo existente (por ejemplo, cambiar su nombre, coordenadas en el canvas o actualizar sus contenidos).")
def update_nodo(proyecto_id: int, nodo_id: int, nodo_data: diseno_conceptual_schema.NodoPantallaUpdate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.update_nodo(db, nodo_id, nodo_data)

@router.delete("/nodos/{nodo_id}", summary="Eliminar un Nodo y todos sus contenidos anidados", description="Borra un nodo del canvas y todos sus contenidos anidados, además de las conexiones que lo involucren.")
def delete_nodo(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.delete_nodo(db, nodo_id)

# --- CONEXIONES ---
@router.get("/conexiones", response_model=List[diseno_conceptual_schema.NodoConexionResponse], summary="Listar las líneas de Conexión entre Nodos", description="Lista todas las conexiones o líneas trazadas entre los distintos nodos del mapa conceptual.")
def get_conexiones(proyecto_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.get_conexiones(db, proyecto_id)

@router.post("/conexiones", response_model=diseno_conceptual_schema.NodoConexionResponse, summary="Crear una línea de Conexión (Origen a Destino)", description="Crea una nueva línea de conexión entre un nodo de origen y un nodo de destino.")
def create_conexion(proyecto_id: int, conexion_data: diseno_conceptual_schema.NodoConexionCreate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.create_conexion(db, proyecto_id, conexion_data)

@router.delete("/conexiones/{conexion_id}", summary="Eliminar una línea de Conexión del Canvas", description="Elimina una conexión específica entre dos nodos.")
def delete_conexion(proyecto_id: int, conexion_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.delete_conexion(db, conexion_id)

# --- INVENTARIO GLOBAL ---
@router.get("/inventario", response_model=List[diseno_conceptual_schema.ContenidoItemResponse], summary="Listar Elementos de Inventario (Flotantes sin Nodo)", description="Lista todos los elementos de contenido (textos, imágenes) que están flotantes en el proyecto y que aún no han sido asignados a ningún nodo.")
def get_inventario(proyecto_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.get_inventario(db, proyecto_id)

@router.post("/inventario", response_model=diseno_conceptual_schema.ContenidoItemResponse, summary="Crear un Elemento de Contenido en el Inventario suelto", description="Crea un nuevo contenido suelto en el panel general sin asociarlo de inmediato a una pantalla específica.")
def create_contenido_inventario(proyecto_id: int, contenido_data: diseno_conceptual_schema.ContenidoItemCreate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.create_contenido_inventario(db, proyecto_id, contenido_data)

# --- WIREFRAMES ---
@router.get("/wireframes", response_model=List[diseno_conceptual_schema.WireframeResponse], summary="Listar Archivos Wireframes del Diseño Conceptual", description="Lista todos los wireframes asociados a la Fase 2 del proyecto.")
def get_wireframes(proyecto_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.get_wireframes(db, proyecto_id)

@router.post("/wireframes", response_model=diseno_conceptual_schema.WireframeResponse, summary="Subir un Wireframe", description="Sube un archivo como wireframe para la Fase 2")
def create_wireframe(proyecto_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    return diseno_conceptual_service.create_wireframe(db, proyecto_id, file)


# --- INVENTARIO ADICIONAL ---
@router.put("/inventario/{item_id}", response_model=diseno_conceptual_schema.ContenidoItemResponse, summary="Actualizar Elemento de Inventario", description="Actualiza un elemento (por ejemplo, para asignarle un nodo_id).")
def update_contenido_inventario(proyecto_id: int, item_id: int, item_data: diseno_conceptual_schema.ContenidoItemUpdate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.update_contenido_inventario(db, item_id, item_data)

@router.delete("/inventario/{item_id}", summary="Eliminar Elemento de Inventario")
def delete_contenido_inventario(proyecto_id: int, item_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.delete_contenido_inventario(db, item_id)

# --- WIREFRAMES ADICIONAL ---
@router.delete("/wireframes/{wireframe_id}", summary="Eliminar Wireframe")
def delete_wireframe(proyecto_id: int, wireframe_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.delete_wireframe(db, wireframe_id)

# --- PHASE 2 CHECKLIST (PROYECTO) ---
@router.get("/checklist", response_model=List[diseno_conceptual_schema.DisenoConceptualChecklistItemResponse], summary="Listar Checklist de la Fase 2")
def get_project_checklist(proyecto_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.get_project_checklist(db, proyecto_id)


@router.post("/checklist/regenerate", response_model=List[diseno_conceptual_schema.DisenoConceptualChecklistItemResponse], summary="Regenerar Checklist de la Fase 2")
def regenerate_project_checklist(proyecto_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.regenerate_project_checklist(db, proyecto_id)

@router.post("/checklist", response_model=diseno_conceptual_schema.DisenoConceptualChecklistItemResponse, summary="Añadir Item al Checklist de la Fase 2")
def create_project_checklist_item(proyecto_id: int, item_data: diseno_conceptual_schema.DisenoConceptualChecklistItemCreate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.create_project_checklist_item(db, proyecto_id, item_data)

@router.put("/checklist/{item_id}", response_model=diseno_conceptual_schema.DisenoConceptualChecklistItemResponse, summary="Actualizar Item del Checklist de la Fase 2")
def update_project_checklist_item(proyecto_id: int, item_id: int, item_data: diseno_conceptual_schema.DisenoConceptualChecklistItemUpdate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.update_project_checklist_item(db, item_id, item_data)

@router.delete("/checklist/{item_id}", summary="Eliminar Item del Checklist de la Fase 2")
def delete_project_checklist_item(proyecto_id: int, item_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.delete_project_checklist_item(db, item_id)

# --- WIREFRAME CHECKLIST ---
@router.get("/wireframes/{wireframe_id}/checklist", response_model=List[diseno_conceptual_schema.WireframeChecklistItemResponse], summary="Listar Checklist de un Wireframe especifico")
def get_wireframe_checklist(proyecto_id: int, wireframe_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.get_wireframe_checklist(db, wireframe_id)

@router.post("/wireframes/{wireframe_id}/checklist", response_model=diseno_conceptual_schema.WireframeChecklistItemResponse, summary="Añadir Item al Checklist de un Wireframe")
def create_wireframe_checklist_item(proyecto_id: int, wireframe_id: int, item_data: diseno_conceptual_schema.WireframeChecklistItemCreate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.create_wireframe_checklist_item(db, wireframe_id, item_data)

@router.put("/wireframes/{wireframe_id}/checklist/{item_id}", response_model=diseno_conceptual_schema.WireframeChecklistItemResponse, summary="Actualizar Item del Checklist de un Wireframe")
def update_wireframe_checklist_item(proyecto_id: int, wireframe_id: int, item_id: int, item_data: diseno_conceptual_schema.WireframeChecklistItemUpdate, db: Session = Depends(get_db)):
    return diseno_conceptual_service.update_wireframe_checklist_item(db, item_id, item_data)

@router.delete("/wireframes/{wireframe_id}/checklist/{item_id}", summary="Eliminar Item del Checklist de un Wireframe")
def delete_wireframe_checklist_item(proyecto_id: int, wireframe_id: int, item_id: int, db: Session = Depends(get_db)):
    return diseno_conceptual_service.delete_wireframe_checklist_item(db, item_id)
