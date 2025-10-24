from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ===== EstadoAnimo Schemas =====
class EstadoAnimoBase(BaseModel):
    nivel: int
    notas_texto: Optional[str] = None


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
    nombre: str
    telefono: str
    timezone: Optional[str] = "UTC"


class UsuarioCreate(UsuarioBase):
    pass


class Usuario(UsuarioBase):
    id: int
    nivel_CMV: str
    preferencias_tracking: str
    frecuencia_checkins: str
    fecha_registro: datetime
    
    class Config:
        orm_mode = True


# ===== Habito Schemas =====
class HabitoBase(BaseModel):
    nombre_habito: str
    categoria: Optional[str] = None
    objetivo_semanal: Optional[int] = 0
    activo: Optional[bool] = True


class HabitoCreate(HabitoBase):
    pass


class HabitoUpdate(BaseModel):
    nombre_habito: Optional[str] = None
    categoria: Optional[str] = None
    objetivo_semanal: Optional[int] = None
    activo: Optional[bool] = None


class Habito(HabitoBase):
    id: int
    usuario_id: int
    fecha_creacion: datetime

    class Config:
        orm_mode = True


# ===== RegistroHabito Schemas =====
class RegistroHabitoBase(BaseModel):
    habito_id: int
    completado: Optional[bool] = True
    notas: Optional[str] = None


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
    mensaje_usuario: str
    respuesta_loki: Optional[str] = None
    entidades_extraidas: Optional[str] = None
    categorias_detectadas: Optional[str] = None


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
    factor: str
    impacto_animo: float
    confianza_estadistica: float
    num_datos: int


class CorrelacionCreate(CorrelacionBase):
    pass


class Correlacion(CorrelacionBase):
    id: int
    usuario_id: int
    fecha_calculo: datetime

    class Config:
        orm_mode = True