from sqlalchemy import Column, String, DateTime, text, BigInteger, Integer, ForeignKey
from app.core.database import Base

class Archivo(Base):
    __tablename__ = "archivos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    fase_id = Column(Integer, nullable=True)
    contexto_tipo = Column(String(40), nullable=True)
    contexto_id = Column(BigInteger, nullable=True)
    nombre_original = Column(String(255), nullable=False)
    ruta_almacenamiento = Column(String(500), nullable=False)
    mime_type = Column(String(120), nullable=True)
    tamano_bytes = Column(Integer, nullable=True)
    subido_por = Column(Integer, ForeignKey("users.id"), nullable=False)
    subido_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
