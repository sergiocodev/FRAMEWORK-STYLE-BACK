import google.generativeai as genai
import PIL.Image
import json
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
import asyncio
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from app.models.diseno_detallado_model import DisenoDetalladoArchivo, DisenoDetalladoAlerta, DisenoDetalladoChecklistItem, EstadoDiseno, TipoAlerta
from app.models.file_model import Archivo
import uuid
import os
import shutil

UPLOAD_DIR = "uploads/diseno_detallado/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def upload_and_analyze_design(db: Session, proyecto_id: int, nodo_id: int, file: UploadFile):
    # Guardar archivo fisicamente
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Registrar archivo en DB
    db_archivo = Archivo(
        proyecto_id=proyecto_id,
        nombre_original=file.filename,
        ruta_almacenamiento=file_path,
        mime_type=file.content_type,
        tamano_bytes=os.path.getsize(file_path),
        subido_por=1
    )
    db.add(db_archivo)
    db.commit()
    db.refresh(db_archivo)

    # Eliminar disenio anterior si existe para este nodo
    existing_diseno = db.query(DisenoDetalladoArchivo).filter(DisenoDetalladoArchivo.nodo_id == nodo_id).first()
    if existing_diseno:
        db.delete(existing_diseno)
        db.commit()

    # Registrar Diseno
    db_diseno = DisenoDetalladoArchivo(
        nodo_id=nodo_id,
        archivo_id=db_archivo.id,
        estado=EstadoDiseno.en_revision
    )
    db.add(db_diseno)
    db.commit()
    db.refresh(db_diseno)

    # Simular analisis de IA
    await simulate_ai_analysis(db, db_diseno.id, proyecto_id, file_path)
    
    db.refresh(db_diseno)
    return db_diseno

async def simulate_ai_analysis(db: Session, diseno_id: int, proyecto_id: int, file_path: str):
    from app.models.diseno_visual_model import ColorItem, TypographyItem, DisenoVisualConfig
    
    colores = db.query(ColorItem).filter(ColorItem.proyecto_id == proyecto_id).order_by(ColorItem.orden).all()
    tipografias = db.query(TypographyItem).filter(TypographyItem.proyecto_id == proyecto_id).order_by(TypographyItem.orden).all()
    
    config = db.query(DisenoVisualConfig).filter(DisenoVisualConfig.proyecto_id == proyecto_id).first()
    
    preguntas = []
    if not colores and not tipografias:
        preguntas = ["Colores aplicados correctamente", "Tipografías aplicadas correctamente", "Iconografía aplicada correctamente", "Espaciado y alineación general correcta"]
    else:
        for c in colores:
            preguntas.append(f"Color {c.uso} ({c.hex_code}) aplicado")
        for t in tipografias:
            preguntas.append(f"Tipografía {t.estilo} ({t.tamano_px}px) aplicada")
            
        if config:
            preguntas.append(f"Iconografía ({config.estilo_iconos}, {config.grosor_iconos}px) aplicada")
            preguntas.append(f"Espaciado ({config.escala_espaciado_base}px) y cuadrícula ({config.grid_columnas} col) correctos")
        else:
            preguntas.append("Iconografía aplicada correctamente")
            preguntas.append("Espaciado y alineación general correcta")
        
    api_key = settings.GEMINI_API_KEY
    try:
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            prompt = f'''Eres un analista experto de UI/UX evaluando un prototipo visual de alta fidelidad.
Tu objetivo es verificar si el diseo de la imagen cumple estrictamente con el sistema de diseo especificado y generar un reporte de alertas y check de validacion.
Devuelve EXACTAMENTE un objeto JSON valido con el siguiente formato:
{{
  "alertas": [
    {{"tipo": "error|warning|info", "elemento": "Ej: Boton primario", "mensaje": "Breve descripcion del error visual", "detectado": "Valor encontrado (ej: #FF0000)", "esperado": "Valor esperado (ej: #00FF00)"}}
  ],
  "checklist": {{
    "Pregunta Exacta": "aprobado|rechazado"
  }}
}}

PREGUNTAS DE CHECKLIST A EVALUAR:
{json.dumps(preguntas)}

Por cada pregunta en el checklist, evalua la imagen y asigna "aprobado" si cumple o "rechazado" si no.
Ademas, genera de 1 a 3 alertas si encuentras desviaciones notables de UX/UI.'''

            def _call_gemini():
                img = PIL.Image.open(file_path)
                return model.generate_content([prompt, img])
                
            response = await run_in_threadpool(_call_gemini)
            
            # Limpiar markdown
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            data = json.loads(text)
            
            for al in data.get("alertas", []):
                alerta = DisenoDetalladoAlerta(
                    diseno_archivo_id=diseno_id,
                    tipo=al.get("tipo", "info"),
                    elemento=al.get("elemento", ""),
                    mensaje=al.get("mensaje", ""),
                    detectado=al.get("detectado", ""),
                    esperado=al.get("esperado", "")
                )
                db.add(alerta)
                
            checklist_res = data.get("checklist", {})
            for p in preguntas:
                estado = checklist_res.get(p, "pendiente")
                check = DisenoDetalladoChecklistItem(
                    diseno_archivo_id=diseno_id,
                    pregunta=p,
                    estado=estado
                )
                db.add(check)
                
            db.commit()
            return
    except Exception as e:
        import traceback
        with open("ai_error.log", "w") as f_err:
            traceback.print_exc(file=f_err)
        db.rollback()
        
    # Fallback en caso de error de IA o no api key
    for p in preguntas:
        db.add(DisenoDetalladoChecklistItem(diseno_archivo_id=diseno_id, pregunta=p, estado="pendiente"))
    db.commit()

def get_screen_design(db: Session, nodo_id: int):
    return db.query(DisenoDetalladoArchivo).filter(DisenoDetalladoArchivo.nodo_id == nodo_id).first()

def delete_design(db: Session, nodo_id: int):
    diseno = db.query(DisenoDetalladoArchivo).filter(DisenoDetalladoArchivo.nodo_id == nodo_id).first()
    if diseno:
        db.delete(diseno)
        db.commit()
        return True
    return False
