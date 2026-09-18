from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas import client_schema
from app.services import client_service

router = APIRouter(
    prefix="/api/v1/clientes",
    tags=["Clientes"]
)

@router.get("", response_model=List[client_schema.ClienteResponse])
def list_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return client_service.get_clients(db, skip=skip, limit=limit)

@router.post("", response_model=client_schema.ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(client_in: client_schema.ClienteCreate, db: Session = Depends(get_db)):
    return client_service.create_client(db, client_in)
