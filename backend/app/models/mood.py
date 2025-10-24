from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
import datetime

from app.db.session import Base

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    telefono = Column(String, unique=True, index=True, nullable=False)
    timezone = Column(String, default='UTC')
    nivel_CMV = Column(String, default='inicial')
    preferencias_tracking = Column(Text, default='{}')
    frecuencia_checkins = Column(String, default='diaria')
    fecha_registro = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    estados_animo = relationship("EstadoAnimo", back_populates="usuario", cascade="all, delete-orphan")
    habitos = relationship("Habito", back_populates="usuario", cascade="all, delete-orphan")
    registros_habitos = relationship("RegistroHabito", back_populates="usuario", cascade="all, delete-orphan")
    conversaciones = relationship("ConversacionContexto", back_populates="usuario", cascade="all, delete-orphan")
    correlaciones = relationship("Correlacion", back_populates="usuario", cascade="all, delete-orphan")


class EstadoAnimo(Base):
    __tablename__ = 'estados_animo'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    nivel = Column(Integer, nullable=False)  # Nivel de 1 a 10
    notas_texto = Column(Text, nullable=True)
    contexto_extraido = Column(Text, nullable=True)
    disparadores_detectados = Column(Text, nullable=True)

    usuario = relationship("Usuario", back_populates="estados_animo")


class Habito(Base):
    __tablename__ = 'habitos'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    nombre_habito = Column(String, nullable=False)
    categoria = Column(String, nullable=True)  # ej: ejercicio, social, sueño, trabajo
    objetivo_semanal = Column(Integer, default=0)  # Número de veces por semana
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    usuario = relationship("Usuario", back_populates="habitos")
    registros = relationship("RegistroHabito", back_populates="habito", cascade="all, delete-orphan")


class RegistroHabito(Base):
    __tablename__ = 'registros_habitos'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    habito_id = Column(Integer, ForeignKey('habitos.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    completado = Column(Boolean, default=True)
    notas = Column(Text, nullable=True)

    usuario = relationship("Usuario", back_populates="registros_habitos")
    habito = relationship("Habito", back_populates="registros")


class ConversacionContexto(Base):
    __tablename__ = 'conversaciones_contexto'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    mensaje_usuario = Column(Text, nullable=False)
    respuesta_loki = Column(Text, nullable=True)
    entidades_extraidas = Column(Text, nullable=True)  # JSON como string
    categorias_detectadas = Column(Text, nullable=True)  # JSON como string

    usuario = relationship("Usuario", back_populates="conversaciones")


class Correlacion(Base):
    __tablename__ = 'correlaciones'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    factor = Column(String, nullable=False)  # ej: "ejercicio", "dormir_bien"
    impacto_animo = Column(Float, nullable=False)  # Correlación: -1 a 1
    confianza_estadistica = Column(Float, nullable=False)  # 0 a 1
    num_datos = Column(Integer, default=0)  # Cantidad de datos usados para calcular
    fecha_calculo = Column(DateTime, default=datetime.datetime.utcnow)

    usuario = relationship("Usuario", back_populates="correlaciones")
