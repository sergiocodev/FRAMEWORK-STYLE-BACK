import os
import uuid
import shutil
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.models.diseno_conceptual_model import NodoPantalla, NodoConexion, ContenidoItem, Wireframe, WireframeChecklistItem
from app.schemas.diseno_conceptual_schema import (
    NodoPantallaCreate, NodoPantallaUpdate, NodoConexionCreate,
    ContenidoItemCreate, WireframeCreate, ContenidoItemUpdate, WireframeChecklistItemUpdate, WireframeChecklistItemCreate
)

# --- NODOS (PANTALLAS) ---
def get_nodos(db: Session, proyecto_id: int):
    return db.query(NodoPantalla).filter(NodoPantalla.proyecto_id == proyecto_id, NodoPantalla.fase_creacion == 2).all()

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

def create_wireframe(db: Session, proyecto_id: int, file: UploadFile):
    from app.models.file_model import Archivo
    import uuid
    import shutil
    import os
    
    UPLOAD_DIR_WF = "uploads/wireframes/"
    os.makedirs(UPLOAD_DIR_WF, exist_ok=True)
    
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "png"
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR_WF, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    nuevo_archivo = Archivo(
        proyecto_id=proyecto_id,
        nombre_original=file.filename,
        ruta_almacenamiento=file_path,
        subido_por=1
    )
    db.add(nuevo_archivo)
    db.commit()
    db.refresh(nuevo_archivo)

    new_wireframe = Wireframe(
        proyecto_id=proyecto_id,
        archivo_id=nuevo_archivo.id,
        version="v1",
        generado_por_ia=False
    )
    db.add(new_wireframe)
    db.commit()
    
    db.refresh(new_wireframe)
    
    # Generate default checklist items for wireframe
    default_items = [
            "¿Los elementos principales se reflejan de forma simétrica respecto al eje vertical, horizontal o radial?",
            "¿Los bloques similares conservan relaciones de tamaño consistentes entre sí?",
            "¿Los elementos de la pantalla se ven distribuidos de manera equilibrada, sin que una zona se vea demasiado cargada o vacía en comparación con las demás?",
            "¿La pantalla contiene solo los elementos necesarios y estos se ven ordenados y ubicados de forma consistente?"
        ]
    
    for pregunta in default_items:
        chk = WireframeChecklistItem(
            wireframe_id=new_wireframe.id,
            pregunta=pregunta,
            origen="manual",
            estado="pendiente"
        )
        db.add(chk)
    db.commit()

    return new_wireframe


def get_wireframes(db: Session, proyecto_id: int):
    return db.query(Wireframe).filter(Wireframe.proyecto_id == proyecto_id).all()

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
    items = db.query(DisenoConceptualChecklistItem).filter(DisenoConceptualChecklistItem.proyecto_id == proyecto_id).all()
    if not items:
        from app.models.investigation_model import ArquetipoUsuario, InvestigacionInforme
        from app.models.diseno_conceptual_model import OrigenChecklist, EstadoChecklist
        from app.core.config import settings
        import json
        
        arquetipos = db.query(ArquetipoUsuario).filter(ArquetipoUsuario.proyecto_id == proyecto_id).all()
        informe = db.query(InvestigacionInforme).filter(InvestigacionInforme.proyecto_id == proyecto_id).first()
        
        context = "Investigación de Fase 1:\n"
        if informe:
            context += f"- Problema: {informe.problema or 'N/A'}\n"
            context += f"- Objetivo: {informe.objetivo or 'N/A'}\n"
            context += f"- Producto: {informe.producto or 'N/A'}\n"
            context += f"- Expectativas: {informe.expectativas or 'N/A'}\n"
            context += f"- Restricciones: {informe.restricciones or 'N/A'}\n"
        
        context += "\nArquetipos de Usuario:\n"
        for arq in arquetipos:
            context += f"- {arq.nombre} ({arq.etiqueta}): "
            needs = [n.descripcion for n in arq.necesidades]
            context += ", ".join(needs) if needs else "Sin necesidades"
            context += "\n"

        api_key = settings.GEMINI_API_KEY
        checklist_list = []
        
        if not api_key or api_key == "TU_API_KEY_AQUI":
            checklist_list = ["Error: Falta configurar GEMINI_API_KEY en .env para usar la IA."]
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(settings.GEMINI_MODEL)
                
                prompt = f'''Eres un analista de UX/UI evaluando un diseo conceptual de sistema (baja fidelidad). Tu tarea es generar un checklist estrictamente basado en la investigación proporcionada.
                
                REGLAS CRÍTICAS:
                1. NO inventes funcionalidades. Traduce ÚNICAMENTE lo que está explícitamente escrito en el contexto a ítems de interfaz. Si la investigación tiene 2 datos, genera 2 o 3 ítems.
                2. Es un checklist del diseo conceptual general del sistema (estructura y flujos clave), no de diseño final.
                3. Cada ítem debe ser una condición accionable y corta referida a TODO el sistema en conjunto (ej. "El sistema incluye la navegación al inventario").
                
                Devuelve ESTRÍCTAMENTE un array JSON de strings.
                
                Contexto de Investigación:
                {context}'''
                
                response = model.generate_content(prompt)
                text = response.text
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0]
                elif '```' in text:
                    text = text.split('```')[1].split('```')[0]
                    
                checklist_list = json.loads(text.strip())
            except Exception as e:
                print("Error llamando a Gemini:", e)
                checklist_list = [f"Error al generar con IA: {str(e)}"]
                
        created_any = False
        for desc in checklist_list:
            new_item = DisenoConceptualChecklistItem(
                proyecto_id=proyecto_id,
                pregunta=desc[:255],
                origen=OrigenChecklist.ia,
                estado=EstadoChecklist.pendiente
            )
            db.add(new_item)
            created_any = True
            
        if created_any:
            db.commit()
            items = db.query(DisenoConceptualChecklistItem).filter(DisenoConceptualChecklistItem.proyecto_id == proyecto_id).all()
            
    return items


def regenerate_project_checklist(db: Session, proyecto_id: int):
    db.query(DisenoConceptualChecklistItem).filter(DisenoConceptualChecklistItem.proyecto_id == proyecto_id).delete()
    db.commit()
    return get_project_checklist(db, proyecto_id)

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



