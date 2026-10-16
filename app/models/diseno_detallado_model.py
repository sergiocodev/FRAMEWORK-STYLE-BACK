from sqlalchemy import Column, Integer, String, DateTime, text, BigInteger, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.diseno_conceptual_model import NodoPantalla
from app.models.file_model import Archivo
import enum

class TipoAlerta(str, enum.Enum):
    error = "error"
    warning = "warning"
    info = "info"

class EstadoDiseno(str, enum.Enum):
    pendiente = "pendiente"
    en_revision = "en_revision"
    verificado = "verificado"

class DisenoDetalladoArchivo(Base):
    __tablename__ = "diseno_detallado_archivos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nodo_id = Column(BigInteger, ForeignKey("nodos_pantalla.id", ondelete="CASCADE"), nullable=False, unique=True)
    archivo_id = Column(BigInteger, ForeignKey("archivos.id", ondelete="CASCADE"), nullable=False)
    estado = Column(Enum(EstadoDiseno), default=EstadoDiseno.en_revision)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    actualizado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    nodo = relationship("NodoPantalla")
    archivo = relationship("Archivo")
    alertas = relationship("DisenoDetalladoAlerta", back_populates="diseno_archivo", cascade="all, delete-orphan")

class DisenoDetalladoAlerta(Base):
    __tablename__ = "diseno_detallado_alertas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diseno_archivo_id = Column(BigInteger, ForeignKey("diseno_detallado_archivos.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(Enum(TipoAlerta), default=TipoAlerta.info)
    elemento = Column(String(255), nullable=False)
    mensaje = Column(String(500), nullable=False)
    detectado = Column(String(100), nullable=True)
    esperado = Column(String(100), nullable=True)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    diseno_archivo = relationship("DisenoDetalladoArchivo", back_populates="alertas")
class DisenoDetalladoChecklistItem(Base):
    __tablename__ = "diseno_detallado_checklist_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diseno_archivo_id = Column(BigInteger, ForeignKey("diseno_detallado_archivos.id", ondelete="CASCADE"), nullable=False)
    pregunta = Column(String(255), nullable=False)
    estado = Column(String(50), nullable=False, default="pendiente")
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    diseno_archivo = relationship("DisenoDetalladoArchivo")
