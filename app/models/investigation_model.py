from sqlalchemy import Column, String, DateTime, text, BigInteger, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class InvestigacionInforme(Base):
    __tablename__ = "investigacion_informe"

    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True)
    problema = Column(Text, nullable=True)
    objetivo = Column(Text, nullable=True)
    producto = Column(Text, nullable=True)
    expectativas = Column(Text, nullable=True)
    referencias = Column(JSON, nullable=True)
    analisis_actual = Column(Text, nullable=True)
    restricciones = Column(Text, nullable=True)
    identidad_marca = Column(JSON, nullable=True)
    conclusiones_fase2 = Column(Text, nullable=True)
    actualizado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    proyecto = relationship("Proyecto", back_populates="informe")

class ArquetipoUsuario(Base):
    __tablename__ = "arquetipos_usuario"
    __table_args__ = {'comment': 'Perfiles representativos de los usuarios finales (ej. Estudiante, Docente). Ayudan a enfocar el diseño en sus necesidades reales.'}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(120), nullable=False)
    etiqueta = Column(String(60), nullable=True)
    avatar_archivo_id = Column(BigInteger, ForeignKey("archivos.id", ondelete="SET NULL"), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    orden = Column(Integer, default=0)

    proyecto = relationship("Proyecto", back_populates="arquetipos")
    necesidades = relationship("ArquetipoNecesidad", back_populates="arquetipo", cascade="all, delete-orphan")

class ArquetipoNecesidad(Base):
    __tablename__ = "arquetipo_necesidades"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    arquetipo_id = Column(BigInteger, ForeignKey("arquetipos_usuario.id", ondelete="CASCADE"), nullable=False)
    descripcion = Column(String(255), nullable=False)
    orden = Column(Integer, default=0)

    arquetipo = relationship("ArquetipoUsuario", back_populates="necesidades")
