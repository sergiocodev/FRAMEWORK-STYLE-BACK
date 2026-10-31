from sqlalchemy import Column, Integer, String, DateTime, text, BigInteger, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class EvaluacionEstetica(Base):
    __tablename__ = "evaluaciones_esteticas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, unique=True)
    metodo_seleccionado = Column(String(100), default="Revisión Heurística (Checklist)")
    estado = Column(String(50), default="en_proceso")
    encuesta_url = Column(String(255), default="https://style-eval.com/survey/abc123")
    total_respuestas = Column(Integer, default=12)
    respuestas_completadas = Column(Integer, default=12)
    conclusion_estado = Column(String(50), default="Aprobado")
    conclusion_texto = Column(Text, nullable=True)

    checklist = Column(JSON, nullable=True)
    visawi_metricas = Column(JSON, nullable=True)
    calista_metricas = Column(JSON, nullable=True)
    justificaciones = Column(JSON, nullable=True)

    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    actualizado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    proyecto = relationship("Proyecto", back_populates="evaluacion_estetica")
    hallazgos = relationship("EvaluacionHallazgo", back_populates="evaluacion", cascade="all, delete-orphan", order_by="EvaluacionHallazgo.id.desc()")


class EvaluacionHallazgo(Base):
    __tablename__ = "evaluacion_hallazgos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    evaluacion_id = Column(BigInteger, ForeignKey("evaluaciones_esteticas.id", ondelete="CASCADE"), nullable=False)
    problema = Column(Text, nullable=False)
    severidad = Column(String(50), default="mayor")  # critico, mayor, menor
    fase_origen = Column(Integer, default=3)        # 1, 2, 3, 4
    fase_origen_nombre = Column(String(100), default="Diseño Visual")
    resuelto = Column(Boolean, default=False)
    creado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    evaluacion = relationship("EvaluacionEstetica", back_populates="hallazgos")
