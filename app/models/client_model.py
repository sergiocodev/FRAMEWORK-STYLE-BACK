from sqlalchemy import Column, String, DateTime, text, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(160), nullable=False)
    contacto_nombre = Column(String(120), nullable=True)
    contacto_correo = Column(String(160), nullable=True)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    proyectos = relationship("Proyecto", back_populates="cliente")
