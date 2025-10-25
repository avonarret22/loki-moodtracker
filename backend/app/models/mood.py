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

    # Sistema de niveles de confianza
    nivel_confianza = Column(Integer, default=1)  # 1-5: Conociendo, Estableciendo, Construyendo, Consolidado, Íntimo
    total_interacciones = Column(Integer, default=0)  # Contador de mensajes intercambiados

    # Relationships
    estados_animo = relationship("EstadoAnimo", back_populates="usuario", cascade="all, delete-orphan")
    habitos = relationship("Habito", back_populates="usuario", cascade="all, delete-orphan")
    registros_habitos = relationship("RegistroHabito", back_populates="usuario", cascade="all, delete-orphan")
    conversaciones = relationship("ConversacionContexto", back_populates="usuario", cascade="all, delete-orphan")
    correlaciones = relationship("Correlacion", back_populates="usuario", cascade="all, delete-orphan")
    resumenes_conversacion = relationship("ResumenConversacion", back_populates="usuario", cascade="all, delete-orphan")
    perfil = relationship("PerfilUsuario", back_populates="usuario", uselist=False, cascade="all, delete-orphan")
    feedbacks = relationship("FeedbackRespuesta", back_populates="usuario", cascade="all, delete-orphan")
    respuestas_exitosas = relationship("RespuestaExitosa", back_populates="usuario", cascade="all, delete-orphan")


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


class ResumenConversacion(Base):
    __tablename__ = 'resumenes_conversacion'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    fecha_resumen = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    resumen_texto = Column(Text, nullable=False)  # Resumen en lenguaje natural
    temas_principales = Column(Text, nullable=True)  # JSON: lista de temas
    emociones_detectadas = Column(Text, nullable=True)  # JSON: emociones principales
    progreso_emocional = Column(Text, nullable=True)  # JSON: evolución del ánimo
    num_mensajes = Column(Integer, default=0)  # Cantidad de mensajes resumidos
    periodo_inicio = Column(DateTime, nullable=True)  # Cuándo comenzó este período
    periodo_fin = Column(DateTime, nullable=True)  # Cuándo terminó este período

    usuario = relationship("Usuario", back_populates="resumenes_conversacion")


class PerfilUsuario(Base):
    __tablename__ = 'perfil_usuario'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), unique=True, nullable=False)
    preferencias_conversacionales = Column(Text, nullable=True)  # JSON: formal/casual, directo/empático
    temas_sensibles = Column(Text, nullable=True)  # JSON: lista de temas sensibles
    patrones_lenguaje_favoritos = Column(Text, nullable=True)  # JSON: expresiones preferidas
    historial_temas_recurrentes = Column(Text, nullable=True)  # JSON: temas que aparecen frecuentemente
    emociones_primarias_frecuentes = Column(Text, nullable=True)  # JSON: emociones dominantes
    valores_principales = Column(Text, nullable=True)  # JSON: valores detectados
    fecha_actualizacion = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_creacion = Column(DateTime, default=datetime.datetime.utcnow)

    usuario = relationship("Usuario", back_populates="perfil")


class FeedbackRespuesta(Base):
    __tablename__ = 'feedback_respuestas'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    conversacion_id = Column(Integer, ForeignKey('conversaciones_contexto.id'), nullable=True)
    mensaje_usuario = Column(Text, nullable=False)
    respuesta_loki = Column(Text, nullable=False)
    utilidad_rating = Column(Integer, nullable=True)  # 1-5: qué tan útil fue
    ayudo = Column(Boolean, default=False)  # ¿Realmente ayudó?
    notas_feedback = Column(Text, nullable=True)  # Comentarios del usuario
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    usuario = relationship("Usuario", back_populates="feedbacks")


class RespuestaExitosa(Base):
    __tablename__ = 'respuestas_exitosas'

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    patron_pregunta = Column(String, nullable=False)  # Patrón/tipo de pregunta
    respuesta_efectiva = Column(Text, nullable=False)  # La respuesta que funcionó
    veces_usado = Column(Integer, default=1)  # Cuántas veces se usó con éxito
    utilidad_promedio = Column(Float, default=5.0)  # Rating promedio (1-5)
    fecha_descubierta = Column(DateTime, default=datetime.datetime.utcnow)
    fecha_ultima_uso = Column(DateTime, default=datetime.datetime.utcnow)

    usuario = relationship("Usuario", back_populates="respuestas_exitosas")
