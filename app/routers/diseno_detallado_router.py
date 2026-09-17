from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.diseno_detallado_schema import DisenoDetalladoArchivoResponse
from app.services import diseno_detallado_service

router = APIRouter(prefix="/api/proyectos/{proyecto_id}/pantallas/{nodo_id}/diseno-detallado", tags=["Fase 4: Diseño Detallado"])

@router.post("/upload", response_model=DisenoDetalladoArchivoResponse)
async def upload_design(proyecto_id: int, nodo_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    diseno = await diseno_detallado_service.upload_and_analyze_design(db, proyecto_id, nodo_id, file)
    return diseno

@router.get("", response_model=DisenoDetalladoArchivoResponse)
def get_design(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    diseno = diseno_detallado_service.get_screen_design(db, nodo_id)
    if not diseno:
        raise HTTPException(status_code=404, detail="No design found for this screen.")
    # Construir URL para el archivo
    diseno.archivo_url = f"http://localhost:8000/{diseno.archivo.ruta}" if diseno.archivo else None
    return diseno

@router.delete("")
def delete_design(proyecto_id: int, nodo_id: int, db: Session = Depends(get_db)):
    success = diseno_detallado_service.delete_design(db, nodo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Design not found.")
    return {"message": "Design deleted successfully."}

