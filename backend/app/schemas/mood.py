from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
import re
from app.core.validation import (
    sanitize_user_input,
    sanitize_phone_number,
    validate_no_sql_injection,
    validate_no_xss
)


# ===== EstadoAnimo Schemas =====
class EstadoAnimoBase(BaseModel):
    nivel: int = Field(..., ge=1, le=10, description="Nivel de ánimo entre 1 y 10")
    notas_texto: Optional[str] = Field(None, max_length=5000, description="Notas del usuario")

    @field_validator('notas_texto')
    @classmethod
    def sanitize_notas(cls, v):
        if v is None:
            return v
        # Usar sanitización centralizada con validaciones completas
        return sanitize_user_input(
            v,
            max_length=5000,
            allow_html=False,
            check_sql=True,
            check_xss=True
        )


class EstadoAnimoCreate(EstadoAnimoBase):
    pass


class EstadoAnimo(EstadoAnimoBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usuario_id: int
    timestamp: datetime
    contexto_extraido: Optional[str] = None
    disparadores_detectados: Optional[str] = None


# ===== Usuario Schemas =====
class UsuarioBase(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100, description="Nombre del usuario (opcional, Loki lo preguntará)")
    telefono: str = Field(
        ...,
        pattern=r'^\+?[1-9]\d{1,14}$',  # E.164 format (regex -> pattern en Pydantic v2)
        description="Teléfono en formato internacional"
    )
    timezone: Optional[str] = Field(default="UTC", max_length=50)

    @field_validator('nombre')
    @classmethod
    def sanitize_nombre(cls, v):
        if v is None:
            return v
        # Usar sanitización centralizada
        v = sanitize_user_input(v, max_length=100, check_sql=True, check_xss=True)
        # Permitir solo letras, espacios, guiones y apóstrofes
        v = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-\']', '', v)
        v = v.strip()
        if len(v) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        return v

    @field_validator('telefono')
    @classmethod
    def normalize_telefono(cls, v):
        # Usar función centralizada de sanitización de teléfonos
        v = sanitize_phone_number(v)
        if len(v) < 10 or len(v) > 16:
            raise ValueError('Número de teléfono inválido')
        return v


class UsuarioCreate(UsuarioBase):
    pass


class Usuario(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nivel_CMV: str
    preferencias_tracking: str
    frecuencia_checkins: str
    fecha_registro: datetime
    nivel_confianza: Optional[int] = 1
    total_interacciones: Optional[int] = 0


# ===== Habito Schemas =====
class HabitoBase(BaseModel):
    nombre_habito: str = Field(..., min_length=1, max_length=200, description="Nombre del hábito")
    categoria: Optional[str] = Field(None, max_length=100)
    objetivo_semanal: Optional[int] = Field(default=0, ge=0, le=50, description="Objetivo semanal (0-50)")
    activo: Optional[bool] = True

    @field_validator('nombre_habito')
    @classmethod
    def sanitize_nombre_habito(cls, v):
        # Usar sanitización centralizada completa
        v = sanitize_user_input(v, max_length=200, check_sql=True, check_xss=True)
        if len(v) < 1:
            raise ValueError('El nombre del hábito no puede estar vacío')
        return v

    @field_validator('categoria')
    @classmethod
    def sanitize_categoria(cls, v):
        if v is None:
            return v
        return sanitize_user_input(v, max_length=100, check_sql=True, check_xss=True)


class HabitoCreate(HabitoBase):
    pass


class HabitoUpdate(BaseModel):
    nombre_habito: Optional[str] = Field(None, min_length=1, max_length=200)
    categoria: Optional[str] = Field(None, max_length=100)
    objetivo_semanal: Optional[int] = Field(None, ge=0, le=50)
    activo: Optional[bool] = None

    @field_validator('nombre_habito')
    @classmethod
    def sanitize_nombre_habito(cls, v):
        if v is None:
            return v
        v = sanitize_user_input(v, max_length=200, check_sql=True, check_xss=True)
        if len(v) < 1:
            raise ValueError('El nombre del hábito no puede estar vacío')
        return v


class Habito(HabitoBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usuario_id: int
    fecha_creacion: datetime


# ===== RegistroHabito Schemas =====
class RegistroHabitoBase(BaseModel):
    habito_id: int = Field(..., gt=0, description="ID del hábito")
    completado: Optional[bool] = True
    notas: Optional[str] = Field(None, max_length=1000)

    @field_validator('notas')
    @classmethod
    def sanitize_notas(cls, v):
        if v is None:
            return v
        return sanitize_user_input(v, max_length=1000, check_sql=True, check_xss=True)


class RegistroHabitoCreate(RegistroHabitoBase):
    pass


class RegistroHabito(RegistroHabitoBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usuario_id: int
    timestamp: datetime


# ===== ConversacionContexto Schemas =====
class ConversacionContextoBase(BaseModel):
    mensaje_usuario: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")
    respuesta_loki: Optional[str] = Field(None, max_length=10000)
    entidades_extraidas: Optional[str] = Field(None, max_length=5000)
    categorias_detectadas: Optional[str] = Field(None, max_length=1000)

    @field_validator('mensaje_usuario')
    @classmethod
    def validate_mensaje(cls, v):
        # Usar sanitización centralizada completa
        v = sanitize_user_input(v, max_length=2000, check_sql=True, check_xss=True)
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v

    @field_validator('respuesta_loki', 'entidades_extraidas', 'categorias_detectadas')
    @classmethod
    def sanitize_text_fields(cls, v):
        if v is None:
            return v
        # Respuesta Loki y campos extraídos también deben sanitizarse
        max_lengths = {
            'respuesta_loki': 10000,
            'entidades_extraidas': 5000,
            'categorias_detectadas': 1000
        }
        # Usar 5000 como default
        return sanitize_user_input(v, max_length=10000, check_sql=False, check_xss=True)


class ConversacionContextoCreate(ConversacionContextoBase):
    pass


class ConversacionContexto(ConversacionContextoBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usuario_id: int
    timestamp: datetime


# ===== Correlacion Schemas =====
class CorrelacionBase(BaseModel):
    factor: str = Field(..., min_length=1, max_length=200)
    impacto_animo: float = Field(..., ge=-10.0, le=10.0, description="Impacto en el ánimo (-10 a +10)")
    confianza_estadistica: float = Field(..., ge=0.0, le=1.0, description="Confianza estadística (0 a 1)")
    num_datos: int = Field(..., ge=1, description="Número de datos utilizados")

    @field_validator('factor')
    @classmethod
    def sanitize_factor(cls, v):
        v = sanitize_user_input(v, max_length=200, check_sql=True, check_xss=True)
        if len(v) < 1:
            raise ValueError('El factor no puede estar vacío')
        return v


class CorrelacionCreate(CorrelacionBase):
    pass


class Correlacion(CorrelacionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usuario_id: int
    fecha_calculo: datetime


# ===== Chat Message Schema (para el endpoint de chat) =====
class ChatMessage(BaseModel):
    usuario_id: int = Field(..., gt=0, description="ID del usuario")
    mensaje: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")

    @field_validator('mensaje')
    @classmethod
    def validate_mensaje(cls, v):
        # Usar sanitización centralizada completa
        v = sanitize_user_input(v, max_length=2000, check_sql=True, check_xss=True)
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v


class ChatResponse(BaseModel):
    respuesta: str
    contexto: Optional[dict] = None
    mood_detected: Optional[int] = None
    habits_mentioned: Optional[list] = None


# ===== Feedback Schemas =====
class FeedbackCreate(BaseModel):
    conversacion_id: Optional[int] = Field(None, gt=0)
    mensaje_usuario: str = Field(..., min_length=1, max_length=2000)
    respuesta_loki: str = Field(..., min_length=1, max_length=10000)
    utilidad_rating: int = Field(..., ge=1, le=5, description="Rating de utilidad (1-5)")
    ayudo: bool = Field(..., description="¿La respuesta ayudó?")
    notas: Optional[str] = Field(None, max_length=2000)

    @field_validator('mensaje_usuario', 'respuesta_loki', 'notas')
    @classmethod
    def sanitize_text(cls, v):
        if v is None:
            return v
        # Sanitizar todos los campos de texto con validación completa
        return sanitize_user_input(v, max_length=10000, check_sql=True, check_xss=True)
