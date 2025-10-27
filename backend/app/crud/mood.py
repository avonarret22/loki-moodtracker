from sqlalchemy.orm import Session
from typing import Optional

from app.models.mood import Usuario, EstadoAnimo, Habito, RegistroHabito, ConversacionContexto, Correlacion
from app.schemas.mood import (
    UsuarioCreate, EstadoAnimoCreate, HabitoCreate, HabitoUpdate,
    RegistroHabitoCreate, ConversacionContextoCreate, CorrelacionCreate
)


# ===== Usuario CRUD =====
def get_usuario(db: Session, usuario_id: int):
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def get_usuario_by_telefono(db: Session, telefono: str):
    return db.query(Usuario).filter(Usuario.telefono == telefono).first()


def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Usuario).offset(skip).limit(limit).all()


def create_usuario(db: Session, usuario: UsuarioCreate):
    db_usuario = Usuario(**usuario.dict())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def get_or_create_usuario(db: Session, usuario: UsuarioCreate):
    """
    Obtiene un usuario existente o lo crea si no existe.
    Thread-safe para race conditions.
    """
    # Primero intentar obtenerlo
    existing = get_usuario_by_telefono(db, telefono=usuario.telefono)
    if existing:
        return existing
    
    # Si no existe, intentar crearlo
    try:
        return create_usuario(db, usuario=usuario)
    except Exception:
        # Si falla (probablemente por race condition), obtenerlo de nuevo
        db.rollback()
        # Esperar un poco para asegurar que la otra transacción termine
        import time
        time.sleep(0.05)  # 50ms
        existing = get_usuario_by_telefono(db, telefono=usuario.telefono)
        if existing:
            return existing
        raise  # Si aún no existe, re-lanzar el error original


# ===== EstadoAnimo CRUD =====
def get_estado_animo(db: Session, estado_animo_id: int):
    return db.query(EstadoAnimo).filter(EstadoAnimo.id == estado_animo_id).first()


def get_estados_animo_by_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
    return db.query(EstadoAnimo).filter(EstadoAnimo.usuario_id == usuario_id).offset(skip).limit(limit).all()


def create_estado_animo(db: Session, estado_animo: EstadoAnimoCreate, usuario_id: int):
    db_estado_animo = EstadoAnimo(**estado_animo.dict(), usuario_id=usuario_id)
    db.add(db_estado_animo)
    db.commit()
    db.refresh(db_estado_animo)
    return db_estado_animo


# ===== Habito CRUD =====
def get_habito(db: Session, habito_id: int):
    return db.query(Habito).filter(Habito.id == habito_id).first()


def get_habitos_by_usuario(db: Session, usuario_id: int, activo: Optional[bool] = None):
    query = db.query(Habito).filter(Habito.usuario_id == usuario_id)
    if activo is not None:
        query = query.filter(Habito.activo == activo)
    return query.all()


def create_habito(db: Session, habito: HabitoCreate, usuario_id: int):
    db_habito = Habito(**habito.dict(), usuario_id=usuario_id)
    db.add(db_habito)
    db.commit()
    db.refresh(db_habito)
    return db_habito


def update_habito(db: Session, habito_id: int, habito_update: HabitoUpdate):
    db_habito = db.query(Habito).filter(Habito.id == habito_id).first()
    if db_habito:
        update_data = habito_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_habito, key, value)
        db.commit()
        db.refresh(db_habito)
    return db_habito


def delete_habito(db: Session, habito_id: int):
    db_habito = db.query(Habito).filter(Habito.id == habito_id).first()
    if db_habito:
        db.delete(db_habito)
        db.commit()
    return db_habito


# ===== RegistroHabito CRUD =====
def get_registro_habito(db: Session, registro_id: int):
    return db.query(RegistroHabito).filter(RegistroHabito.id == registro_id).first()


def get_registros_habito_by_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
    return db.query(RegistroHabito).filter(RegistroHabito.usuario_id == usuario_id).offset(skip).limit(limit).all()


def get_registros_habito_by_habito(db: Session, habito_id: int, skip: int = 0, limit: int = 100):
    return db.query(RegistroHabito).filter(RegistroHabito.habito_id == habito_id).offset(skip).limit(limit).all()


def create_registro_habito(db: Session, registro: RegistroHabitoCreate, usuario_id: int):
    db_registro = RegistroHabito(**registro.dict(), usuario_id=usuario_id)
    db.add(db_registro)
    db.commit()
    db.refresh(db_registro)
    return db_registro


# ===== ConversacionContexto CRUD =====
def get_conversacion(db: Session, conversacion_id: int):
    return db.query(ConversacionContexto).filter(ConversacionContexto.id == conversacion_id).first()


def get_conversaciones_by_usuario(db: Session, usuario_id: int, skip: int = 0, limit: int = 100):
    return db.query(ConversacionContexto).filter(
        ConversacionContexto.usuario_id == usuario_id
    ).order_by(ConversacionContexto.timestamp.desc()).offset(skip).limit(limit).all()


def create_conversacion(db: Session, conversacion: ConversacionContextoCreate, usuario_id: int):
    db_conversacion = ConversacionContexto(**conversacion.dict(), usuario_id=usuario_id)
    db.add(db_conversacion)
    db.commit()
    db.refresh(db_conversacion)
    return db_conversacion


# ===== Correlacion CRUD =====
def get_correlacion(db: Session, correlacion_id: int):
    return db.query(Correlacion).filter(Correlacion.id == correlacion_id).first()


def get_correlaciones_by_usuario(db: Session, usuario_id: int):
    return db.query(Correlacion).filter(
        Correlacion.usuario_id == usuario_id
    ).order_by(Correlacion.impacto_animo.desc()).all()


def create_correlacion(db: Session, correlacion: CorrelacionCreate, usuario_id: int):
    db_correlacion = Correlacion(**correlacion.dict(), usuario_id=usuario_id)
    db.add(db_correlacion)
    db.commit()
    db.refresh(db_correlacion)
    return db_correlacion


def delete_correlacion(db: Session, correlacion_id: int):
    db_correlacion = db.query(Correlacion).filter(Correlacion.id == correlacion_id).first()
    if db_correlacion:
        db.delete(db_correlacion)
        db.commit()
    return db_correlacion