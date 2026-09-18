from sqlalchemy.orm import Session
from app.models.client_model import Cliente
from app.schemas.client_schema import ClienteCreate

def get_clients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Cliente).offset(skip).limit(limit).all()

def create_client(db: Session, client: ClienteCreate):
    db_client = Cliente(
        nombre=client.nombre,
        contacto_nombre=client.contacto_nombre,
        contacto_correo=client.contacto_correo
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client
