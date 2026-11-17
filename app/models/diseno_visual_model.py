from sqlalchemy import Column, Integer, String, DateTime, text, BigInteger, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class DisenoVisualConfig(Base):
    __tablename__ = "diseno_visual_config"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, unique=True)
    fuente_principal = Column(String(100), default="Inter")
    fuente_secundaria = Column(String(100), default="Roboto")
    estilo_iconos = Column(String(50), default="lineal")
    
    libreria_iconos = Column(String(50), default="Bootstrap Icons")
    grosor_iconos = Column(Float, default=1.5)
    escala_espaciado_base = Column(Integer, default=8)
    radio_borde_base = Column(Integer, default=8)
    grid_columnas = Column(Integer, default=12)
    grid_gutter = Column(Integer, default=16)

    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    actualizado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

class ColorItem(Base):
    __tablename__ = "diseno_visual_colores"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    hex_code = Column(String(7), nullable=False)
    nombre = Column(String(100), nullable=False)
    token_name = Column(String(100), nullable=True)
    uso = Column(String(100), nullable=False) # e.g. Principal, Texto, Fondo
    orden = Column(Integer, default=0)

class TypographyItem(Base):
    __tablename__ = "diseno_visual_tipografias"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    estilo = Column(String(100), nullable=False) # e.g. H1, H2, Cuerpo
    tamano_px = Column(Integer, nullable=False)
    peso = Column(String(50), nullable=False) # e.g. Semibold (600)
    interlineado = Column(Float, nullable=False)
    tipo_fuente = Column(String(50), default="Principal") # Principal o Secundaria
    orden = Column(Integer, default=0)

class IconItem(Base):
    __tablename__ = "diseno_visual_iconos"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(100), nullable=False)
    token_name = Column(String(100), nullable=False) # e.g. icon.custom
    svg_content = Column(Text, nullable=False) # RAW SVG string sin restricción de tamaño
    estilo = Column(String(50), nullable=True) # Lineal, Relleno
