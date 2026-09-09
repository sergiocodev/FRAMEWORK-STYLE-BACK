from sqlalchemy import Column, Integer, String, DateTime, text, BigInteger, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class TipoProyecto(str, enum.Enum):
    nuevo = "nuevo"
    rediseno = "rediseño"

class NivelDiseno(str, enum.Enum):
    bajo = "bajo"
    medio = "medio"
    alto = "alto"

class EstadoProyecto(str, enum.Enum):
    en_proceso = "en_proceso"
    en_espera = "en_espera"
    completado = "completado"
    detenido = "detenido"

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(160), nullable=False)
    contacto_nombre = Column(String(120), nullable=True)
    contacto_correo = Column(String(160), nullable=True)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    proyectos = relationship("Proyecto", back_populates="cliente")

class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    nombre = Column(String(160), nullable=False)
    tipo = Column(Enum(TipoProyecto), nullable=False, default=TipoProyecto.nuevo)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)
    plataforma = Column(String(80), nullable=True)
    nivel_diseno_objetivo = Column(Enum(NivelDiseno), nullable=False, default=NivelDiseno.medio)
    estado = Column(Enum(EstadoProyecto), nullable=False, default=EstadoProyecto.en_proceso)
    fase_actual_id = Column(Integer, nullable=False, default=1)
    responsable_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    actualizado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    cliente = relationship("Cliente", back_populates="proyectos")
    informe = relationship("InvestigacionInforme", back_populates="proyecto", uselist=False)
    arquetipos = relationship("ArquetipoUsuario", back_populates="proyecto")
