from pydantic import BaseModel, Field, validator, constr
from datetime import datetime
from typing import Optional
import re


# ===== EstadoAnimo Schemas =====
class EstadoAnimoBase(BaseModel):
    nivel: int = Field(..., ge=1, le=10, description="Nivel de ánimo entre 1 y 10")
    notas_texto: Optional[str] = Field(None, max_length=5000, description="Notas del usuario")

    @validator('notas_texto')
    def sanitize_notas(cls, v):
        if v is None:
            return v
        # Sanitizar HTML básico
        v = v.replace('<', '&lt;').replace('>', '&gt;')
        # Limitar caracteres especiales peligrosos
        v = re.sub(r'[<>]', '', v)
        return v.strip()[:5000]  # Hard limit


class EstadoAnimoCreate(EstadoAnimoBase):
    pass


class EstadoAnimo(EstadoAnimoBase):
    id: int
    usuario_id: int
    timestamp: datetime
    contexto_extraido: Optional[str] = None
    disparadores_detectados: Optional[str] = None

    class Config:
        orm_mode = True


# ===== Usuario Schemas =====
class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del usuario")
    telefono: str = Field(
        ...,
        regex=r'^\+?[1-9]\d{1,14}$',  # E.164 format
        description="Teléfono en formato internacional"
    )
    timezone: Optional[str] = Field("UTC", max_length=50)

    @validator('nombre')
    def sanitize_nombre(cls, v):
        # Permitir solo letras, espacios, guiones y apóstrofes
        v = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-\']', '', v)
        v = v.strip()
        if len(v) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        return v

    @validator('telefono')
    def normalize_telefono(cls, v):
        # Normalizar formato E.164
        v = re.sub(r'[^\d+]', '', v)  # Remover todo excepto dígitos y +
        if not v.startswith('+'):
            v = '+' + v
        if len(v) < 10 or len(v) > 16:
            raise ValueError('Número de teléfono inválido')
        return v


class UsuarioCreate(UsuarioBase):
    pass


class Usuario(UsuarioBase):
    id: int
    nivel_CMV: str
    preferencias_tracking: str
    frecuencia_checkins: str
    fecha_registro: datetime
    nivel_confianza: Optional[int] = 1
    total_interacciones: Optional[int] = 0

    class Config:
        orm_mode = True


# ===== Habito Schemas =====
class HabitoBase(BaseModel):
    nombre_habito: str = Field(..., min_length=1, max_length=200, description="Nombre del hábito")
    categoria: Optional[str] = Field(None, max_length=100)
    objetivo_semanal: Optional[int] = Field(0, ge=0, le=50, description="Objetivo semanal (0-50)")
    activo: Optional[bool] = True

    @validator('nombre_habito')
    def sanitize_nombre_habito(cls, v):
        # Sanitizar y normalizar
        v = v.strip()
        v = re.sub(r'[<>]', '', v)  # Remover HTML tags
        if len(v) < 1:
            raise ValueError('El nombre del hábito no puede estar vacío')
        return v[:200]  # Hard limit

    @validator('categoria')
    def sanitize_categoria(cls, v):
        if v is None:
            return v
        v = v.strip()
        v = re.sub(r'[<>]', '', v)
        return v[:100]


class HabitoCreate(HabitoBase):
    pass


class HabitoUpdate(BaseModel):
    nombre_habito: Optional[str] = Field(None, min_length=1, max_length=200)
    categoria: Optional[str] = Field(None, max_length=100)
    objetivo_semanal: Optional[int] = Field(None, ge=0, le=50)
    activo: Optional[bool] = None

    @validator('nombre_habito')
    def sanitize_nombre_habito(cls, v):
        if v is None:
            return v
        v = v.strip()
        v = re.sub(r'[<>]', '', v)
        if len(v) < 1:
            raise ValueError('El nombre del hábito no puede estar vacío')
        return v[:200]


class Habito(HabitoBase):
    id: int
    usuario_id: int
    fecha_creacion: datetime

    class Config:
        orm_mode = True


# ===== RegistroHabito Schemas =====
class RegistroHabitoBase(BaseModel):
    habito_id: int = Field(..., gt=0, description="ID del hábito")
    completado: Optional[bool] = True
    notas: Optional[str] = Field(None, max_length=1000)

    @validator('notas')
    def sanitize_notas(cls, v):
        if v is None:
            return v
        v = v.replace('<', '&lt;').replace('>', '&gt;')
        return v.strip()[:1000]


class RegistroHabitoCreate(RegistroHabitoBase):
    pass


class RegistroHabito(RegistroHabitoBase):
    id: int
    usuario_id: int
    timestamp: datetime

    class Config:
        orm_mode = True


# ===== ConversacionContexto Schemas =====
class ConversacionContextoBase(BaseModel):
    mensaje_usuario: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")
    respuesta_loki: Optional[str] = Field(None, max_length=10000)
    entidades_extraidas: Optional[str] = Field(None, max_length=5000)
    categorias_detectadas: Optional[str] = Field(None, max_length=1000)

    @validator('mensaje_usuario')
    def validate_mensaje(cls, v):
        # Sanitizar HTML
        v = v.replace('<', '&lt;').replace('>', '&gt;')
        # Validar que no sea solo espacios
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v.strip()[:2000]  # Hard limit

    @validator('respuesta_loki', 'entidades_extraidas', 'categorias_detectadas')
    def sanitize_text_fields(cls, v):
        if v is None:
            return v
        v = v.replace('<', '&lt;').replace('>', '&gt;')
        return v.strip()


class ConversacionContextoCreate(ConversacionContextoBase):
    pass


class ConversacionContexto(ConversacionContextoBase):
    id: int
    usuario_id: int
    timestamp: datetime

    class Config:
        orm_mode = True


# ===== Correlacion Schemas =====
class CorrelacionBase(BaseModel):
    factor: str = Field(..., min_length=1, max_length=200)
    impacto_animo: float = Field(..., ge=-10.0, le=10.0, description="Impacto en el ánimo (-10 a +10)")
    confianza_estadistica: float = Field(..., ge=0.0, le=1.0, description="Confianza estadística (0 a 1)")
    num_datos: int = Field(..., ge=1, description="Número de datos utilizados")

    @validator('factor')
    def sanitize_factor(cls, v):
        v = v.strip()
        v = re.sub(r'[<>]', '', v)
        if len(v) < 1:
            raise ValueError('El factor no puede estar vacío')
        return v[:200]


class CorrelacionCreate(CorrelacionBase):
    pass


class Correlacion(CorrelacionBase):
    id: int
    usuario_id: int
    fecha_calculo: datetime

    class Config:
        orm_mode = True


# ===== Chat Message Schema (para el endpoint de chat) =====
class ChatMessage(BaseModel):
    usuario_id: int = Field(..., gt=0, description="ID del usuario")
    mensaje: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")

    @validator('mensaje')
    def validate_mensaje(cls, v):
        # Sanitizar HTML
        v = v.replace('<', '&lt;').replace('>', '&gt;')
        # Validar que no sea solo espacios
        if not v.strip():
            raise ValueError('El mensaje no puede estar vacío')
        return v.strip()


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

    @validator('mensaje_usuario', 'respuesta_loki', 'notas')
    def sanitize_text(cls, v):
        if v is None:
            return v
        v = v.replace('<', '&lt;').replace('>', '&gt;')
        return v.strip()
