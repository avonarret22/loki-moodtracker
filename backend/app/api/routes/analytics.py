from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app import crud, schemas

router = APIRouter()


# ===== Endpoints para Conversaciones =====
@router.post("/usuarios/{usuario_id}/conversaciones/", response_model=schemas.ConversacionContexto)
def create_conversacion_for_usuario(
    usuario_id: int, conversacion: schemas.ConversacionContextoCreate, db: Session = Depends(get_db)
):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return crud.create_conversacion(db=db, conversacion=conversacion, usuario_id=usuario_id)


@router.get("/usuarios/{usuario_id}/conversaciones/", response_model=List[schemas.ConversacionContexto])
def read_conversaciones(usuario_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    conversaciones = crud.get_conversaciones_by_usuario(db=db, usuario_id=usuario_id, skip=skip, limit=limit)
    return conversaciones


@router.get("/conversaciones/{conversacion_id}", response_model=schemas.ConversacionContexto)
def read_conversacion(conversacion_id: int, db: Session = Depends(get_db)):
    db_conversacion = crud.get_conversacion(db, conversacion_id=conversacion_id)
    if db_conversacion is None:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return db_conversacion


# ===== Endpoints para Correlaciones =====
@router.post("/usuarios/{usuario_id}/correlaciones/", response_model=schemas.Correlacion)
def create_correlacion_for_usuario(
    usuario_id: int, correlacion: schemas.CorrelacionCreate, db: Session = Depends(get_db)
):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return crud.create_correlacion(db=db, correlacion=correlacion, usuario_id=usuario_id)


@router.get("/usuarios/{usuario_id}/correlaciones/", response_model=List[schemas.Correlacion])
def read_correlaciones(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    correlaciones = crud.get_correlaciones_by_usuario(db=db, usuario_id=usuario_id)
    return correlaciones


@router.get("/correlaciones/{correlacion_id}", response_model=schemas.Correlacion)
def read_correlacion(correlacion_id: int, db: Session = Depends(get_db)):
    db_correlacion = crud.get_correlacion(db, correlacion_id=correlacion_id)
    if db_correlacion is None:
        raise HTTPException(status_code=404, detail="Correlación no encontrada")
    return db_correlacion


@router.delete("/correlaciones/{correlacion_id}")
def delete_correlacion(correlacion_id: int, db: Session = Depends(get_db)):
    db_correlacion = crud.delete_correlacion(db, correlacion_id=correlacion_id)
    if db_correlacion is None:
        raise HTTPException(status_code=404, detail="Correlación no encontrada")
    return {"message": "Correlación eliminada exitosamente"}