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
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "png"
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

    # Analisis optimizado de IA con tokens de la Fase 3
    try:
        await simulate_ai_analysis(db, db_diseno.id, proyecto_id, file_path)
    except Exception as e:
        import traceback
        traceback.print_exc()
    
    db.refresh(db_diseno)
    return db_diseno

async def simulate_ai_analysis(db: Session, diseno_id: int, proyecto_id: int, file_path: str):
    from app.models.diseno_visual_model import ColorItem, TypographyItem, DisenoVisualConfig
    
    colores = db.query(ColorItem).filter(ColorItem.proyecto_id == proyecto_id).order_by(ColorItem.orden).all()
    tipografias = db.query(TypographyItem).filter(TypographyItem.proyecto_id == proyecto_id).order_by(TypographyItem.orden).all()
    config = db.query(DisenoVisualConfig).filter(DisenoVisualConfig.proyecto_id == proyecto_id).first()
    
    preguntas = []
    tokens_resumen = []
    
    if colores:
        for c in colores:
            p_text = f"Color {c.uso} ({c.hex_code}) aplicado"
            preguntas.append(p_text)
            tokens_resumen.append(f"- {c.uso}: {c.hex_code}")
    else:
        preguntas.extend(["Color Principal aplicado correctamente", "Color Secundario aplicado correctamente", "Colores de fondo y superficie consistentes"])
        
    if tipografias:
        for t in tipografias:
            fuente_nom = "Inter"
            if config:
                fuente_nom = config.fuente_principal if t.tipo_fuente == "Principal" else config.fuente_secundaria
            p_text = f"Tipografía {t.estilo} ({t.tamano_px}px) aplicada"
            preguntas.append(p_text)
            tokens_resumen.append(f"- Tipografía {t.estilo}: {t.tamano_px}px ({fuente_nom}, {t.peso})")
    else:
        preguntas.extend(["Jerarquía tipográfica (títulos y subtítulos) clara", "Tipografía de cuerpo legible y consistente"])
        
    if config:
        preguntas.append(f"Iconografía ({config.estilo_iconos}, {config.grosor_iconos}px) aplicada")
        preguntas.append(f"Espaciado ({config.escala_espaciado_base}px) y cuadrícula ({config.grid_columnas} col) correctos")
        tokens_resumen.append(f"- Iconos: estilo {config.estilo_iconos}, grosor {config.grosor_iconos}px")
        tokens_resumen.append(f"- Espaciado base: {config.escala_espaciado_base}px en grilla de {config.grid_columnas} columnas")
    else:
        preguntas.append("Iconografía con estilo y trazo uniforme")
        preguntas.append("Espaciado consistente en múltiplos de 8px")

    api_key = settings.GEMINI_API_KEY
    if api_key:
        try:
            genai.configure(api_key=api_key)
            model_name = settings.GEMINI_MODEL or "gemini-3.1-flash-lite"
            if "/" in model_name:
                model_name = model_name.split("/")[-1]
                
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
            )
            
            prompt = f'''Eres un auditor senior de diseño UI/UX y Design Systems.
Tu misión es verificar si el prototipo visual de la imagen cumple rigurosamente con la Guía de Estilos y Tokens de Diseño acordados en la Fase 3 del framework STYLE.

SISTEMA DE DISEÑO DEL PROYECTO (TOKENS OFICIALES DE FASE 3):
{chr(10).join(tokens_resumen) if tokens_resumen else "Sistema de diseño estándar: Colores corporativos, jerarquía tipográfica 16/24px, grilla de 8px."}

LISTA DE COMPROBACIÓN A EVALUAR:
{json.dumps(preguntas, indent=2)}

INSTRUCCIONES CLAVE DE EVALUACIÓN:
1. Revisa la imagen adjunta. Para cada una de las preguntas de la lista, determina si el prototipo cumple satisfactoriamente ("aprobado") o si no cumple / no se observa ("rechazado").
2. Si la imagen es un boceto en blanco y negro (wireframe en escala de grises) y no tiene estilos de alta fidelidad, rechaza los colores correspondientes y genera una alerta clara indicándolo.
3. Genera entre 1 y 3 alertas específicas con elementos tangibles de la interfaz donde se detecte desalineación, bajo contraste o inconsistencia con la guía visual.
4. Devuelve ÚNICAMENTE un objeto JSON válido con la siguiente estructura:
{{
  "alertas": [
    {{
      "tipo": "error|warning|info",
      "elemento": "Nombre del componente o sección (ej: Botón 'Comprar', Barra de navegación, Título principal)",
      "mensaje": "Descripción breve y clara de la discrepancia visual observada",
      "detectado": "Valor o estilo encontrado en la imagen",
      "esperado": "Valor o token esperado según la guía visual"
    }}
  ],
  "checklist": {{
    "Texto Exacto de la Pregunta": "aprobado|rechazado"
  }}
}}'''

            def _call_gemini():
                img = PIL.Image.open(file_path)
                return model.generate_content([prompt, img])
                
            response = await run_in_threadpool(_call_gemini)
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            data = json.loads(text.strip())
            
            for al in data.get("alertas", []):
                alerta = DisenoDetalladoAlerta(
                    diseno_archivo_id=diseno_id,
                    tipo=al.get("tipo", "info"),
                    elemento=al.get("elemento", "Elemento UI"),
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
            
    # Fallback determinista si no hay Gemini o si falló
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
