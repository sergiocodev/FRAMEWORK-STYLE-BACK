from sqlalchemy import Column, Integer, String, DateTime, text, BigInteger, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class TipoNodo(str, enum.Enum):
    modulo = "modulo"
    pantalla = "pantalla"
    componente = "componente"
    texto = "texto"

class EstadoVerificacion(str, enum.Enum):
    pendiente = "pendiente"
    en_revision = "en_revision"
    verificado = "verificado"

class TipoConexion(str, enum.Enum):
    navegacion = "navegacion"
    jerarquia = "jerarquia"

class TipoContenido(str, enum.Enum):
    texto = "texto"
    imagen = "imagen"
    otro = "otro"

class PrioridadContenido(str, enum.Enum):
    alta = "alta"
    media = "media"
    baja = "baja"

class OrigenChecklist(str, enum.Enum):
    manual = "manual"
    ia = "ia"

class EstadoChecklist(str, enum.Enum):
    pendiente = "pendiente"
    aceptado = "aceptado"
    descartado = "descartado"

class NodoPantalla(Base):
    __tablename__ = "nodos_pantalla"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(120), nullable=False)
    tipo = Column(Enum(TipoNodo), nullable=False, default=TipoNodo.pantalla)
    icono = Column(String(60), nullable=True)
    descripcion = Column(String(255), nullable=True)
    pos_x = Column(Integer, default=0)
    pos_y = Column(Integer, default=0)
    prioridad = Column(String(20), nullable=True)
    estado_verificacion = Column(Enum(EstadoVerificacion), default=EstadoVerificacion.pendiente)
    enlace_diseno_externo = Column(String(500), nullable=True)
    fase_creacion = Column(Integer, default=2)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    actualizado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    # Relaciones
    contenidos = relationship("ContenidoItem", back_populates="nodo")
    wireframes = relationship("Wireframe", back_populates="nodo")

class NodoConexion(Base):
    __tablename__ = "nodo_conexiones"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    nodo_origen_id = Column(BigInteger, ForeignKey("nodos_pantalla.id", ondelete="CASCADE"), nullable=False)
    nodo_destino_id = Column(BigInteger, ForeignKey("nodos_pantalla.id", ondelete="CASCADE"), nullable=False)
    tipo_conexion = Column(Enum(TipoConexion), default=TipoConexion.navegacion)

class ContenidoItem(Base):
    __tablename__ = "contenido_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    nodo_id = Column(BigInteger, ForeignKey("nodos_pantalla.id", ondelete="SET NULL"), nullable=True)
    tipo = Column(Enum(TipoContenido), nullable=False)
    nombre = Column(String(160), nullable=False)
    detalle = Column(String(120), nullable=True)
    prioridad = Column(Enum(PrioridadContenido), nullable=False, default=PrioridadContenido.media)
    archivo_id = Column(BigInteger, ForeignKey("archivos.id", ondelete="SET NULL"), nullable=True)
    orden = Column(Integer, default=0)

    nodo = relationship("NodoPantalla", back_populates="contenidos")
    archivo = relationship("Archivo")

class Wireframe(Base):
    __tablename__ = "wireframes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    nodo_id = Column(BigInteger, ForeignKey("nodos_pantalla.id", ondelete="SET NULL"), nullable=True)
    archivo_id = Column(BigInteger, ForeignKey("archivos.id", ondelete="CASCADE"), nullable=False)
    titulo = Column(String(255), nullable=True)
    version = Column(String(10), default='v1')
    generado_por_ia = Column(Boolean, default=False)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    nodo = relationship("NodoPantalla", back_populates="wireframes")
    archivo = relationship("Archivo")
    checklist_items = relationship("WireframeChecklistItem", back_populates="wireframe", cascade="all, delete-orphan")

    @property
    def archivo_url(self):
        import os
        if self.archivo and getattr(self.archivo, "ruta_almacenamiento", None):
            return f"/uploads/wireframes/{os.path.basename(self.archivo.ruta_almacenamiento)}"
        return None

    @property
    def fileName(self):
        if self.archivo:
            return self.archivo.nombre_original
        return None


class WireframeChecklistItem(Base):
    __tablename__ = "wireframe_checklist_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    wireframe_id = Column(BigInteger, ForeignKey("wireframes.id", ondelete="CASCADE"), nullable=False)
    pregunta = Column(String(255), nullable=False)
    origen = Column(Enum(OrigenChecklist), nullable=False, default=OrigenChecklist.ia)
    estado = Column(Enum(EstadoChecklist), nullable=False, default=EstadoChecklist.pendiente)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    wireframe = relationship("Wireframe", back_populates="checklist_items")


class DisenoConceptualChecklistItem(Base):
    __tablename__ = "diseno_conceptual_checklist_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    pregunta = Column(String(255), nullable=False)
    origen = Column(Enum(OrigenChecklist), nullable=False, default=OrigenChecklist.ia)
    estado = Column(Enum(EstadoChecklist), nullable=False, default=EstadoChecklist.pendiente)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

