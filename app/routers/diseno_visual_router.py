from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import urllib.request
import urllib.parse
import json

from app.core.database import get_db
from app.schemas import diseno_visual_schema as schemas
from app.services import diseno_visual_service as service
from app.services.mssboa_optimizer import MSSBOAOptimizer

router = APIRouter(
    prefix="/api/diseno-visual",
    tags=["Fase 3: Diseño Visual"]
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

@router.post("/{proyecto_id}/tipografias/batch", response_model=List[schemas.TypographyItemResponse])
def replace_tipografias_batch(proyecto_id: int, tipografias_in: List[schemas.TypographyItemCreate], db: Session = Depends(get_db)):
    return service.replace_tipografias(db, proyecto_id, tipografias_in)

@router.post("/iconos", response_model=schemas.IconItemResponse)
def add_icono(icon_in: schemas.IconItemCreate, db: Session = Depends(get_db)):
    return service.add_icono(db, icon_in)

@router.delete("/iconos/{icon_id}")
def delete_icono(icon_id: int, db: Session = Depends(get_db)):
    icon = service.delete_icono(db, icon_id)
    if not icon:
        raise HTTPException(status_code=404, detail="Icon not found")
    return {"message": "Icon deleted"}

@router.post("/{proyecto_id}/colores/batch", response_model=List[schemas.ColorItemResponse])
def replace_colores_batch(proyecto_id: int, colores_in: List[schemas.ColorItemCreate], db: Session = Depends(get_db)):
    return service.replace_colores(db, proyecto_id, colores_in)

@router.post("/optimizador/mssboa", response_model=schemas.MSSBOAOptimizeResponse)
def optimize_palette_mssboa(req: schemas.MSSBOAOptimizeRequest):
    try:
        optimizer = MSSBOAOptimizer(
            base_hex=req.base_hex,
            harmony_type=req.harmony_type or "Complementary",
            mode=req.mode or "light",
            wcag_target=req.wcag_target or "AA",
            population_size=req.population_size or 30,
            max_iterations=req.max_iterations or 50,
            seed=req.seed
        )
        return optimizer.optimize()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en optimizador MSSBOA: {str(e)}")

# =========================================================================
# PROXY PARA ICONOS OPEN SOURCE (Evita bloqueos de CORS y AdBlockers del navegador)
# =========================================================================

@router.get("/catalogo/collection")
def get_icon_collection(prefix: str):
    """Proxy seguro para obtener el listado de nombres de una colección Iconify"""
    try:
        url = f"https://api.iconify.design/collection?prefix={prefix}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al conectar con Iconify: {str(e)}")

@router.get("/catalogo/search")
def search_icons_proxy(prefix: str, query: str = "", limit: int = 48):
    """Proxy seguro para búsqueda de iconos en Iconify"""
    try:
        clean_q = urllib.parse.quote(query.strip())
        url = f"https://api.iconify.design/search?prefix={prefix}&query={clean_q}&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error en búsqueda Iconify: {str(e)}")

@router.get("/catalogo/icons")
def get_icons_batch_proxy(prefix: str, icons: str):
    """Proxy seguro para obtener los cuerpos SVG en lote desde Iconify"""
    try:
        url = f"https://api.iconify.design/{prefix}.json?icons={icons}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al cargar lote SVG de Iconify: {str(e)}")
