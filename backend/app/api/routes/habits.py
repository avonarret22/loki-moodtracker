from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app import crud, schemas

router = APIRouter()


# ===== Endpoints para Hábitos =====
@router.post("/usuarios/{usuario_id}/habitos/", response_model=schemas.Habito)
def create_habito_for_usuario(
    usuario_id: int, habito: schemas.HabitoCreate, db: Session = Depends(get_db)
):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return crud.create_habito(db=db, habito=habito, usuario_id=usuario_id)


@router.get("/usuarios/{usuario_id}/habitos/", response_model=List[schemas.Habito])
def read_habitos(usuario_id: int, activo: bool = None, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    habitos = crud.get_habitos_by_usuario(db=db, usuario_id=usuario_id, activo=activo)
    return habitos


@router.get("/habitos/{habito_id}", response_model=schemas.Habito)
def read_habito(habito_id: int, db: Session = Depends(get_db)):
    db_habito = crud.get_habito(db, habito_id=habito_id)
    if db_habito is None:
        raise HTTPException(status_code=404, detail="Hábito no encontrado")
    return db_habito


@router.put("/habitos/{habito_id}", response_model=schemas.Habito)
def update_habito(habito_id: int, habito_update: schemas.HabitoUpdate, db: Session = Depends(get_db)):
    db_habito = crud.update_habito(db, habito_id=habito_id, habito_update=habito_update)
    if db_habito is None:
        raise HTTPException(status_code=404, detail="Hábito no encontrado")
    return db_habito


@router.delete("/habitos/{habito_id}")
def delete_habito(habito_id: int, db: Session = Depends(get_db)):
    db_habito = crud.delete_habito(db, habito_id=habito_id)
    if db_habito is None:
        raise HTTPException(status_code=404, detail="Hábito no encontrado")
    return {"message": "Hábito eliminado exitosamente"}


# ===== Endpoints para Registros de Hábitos =====
@router.post("/usuarios/{usuario_id}/registros_habitos/", response_model=schemas.RegistroHabito)
def create_registro_habito_for_usuario(
    usuario_id: int, registro: schemas.RegistroHabitoCreate, db: Session = Depends(get_db)
):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que el hábito existe y pertenece al usuario
    db_habito = crud.get_habito(db, habito_id=registro.habito_id)
    if db_habito is None:
        raise HTTPException(status_code=404, detail="Hábito no encontrado")
    if db_habito.usuario_id != usuario_id:
        raise HTTPException(status_code=403, detail="El hábito no pertenece a este usuario")
    
    return crud.create_registro_habito(db=db, registro=registro, usuario_id=usuario_id)


@router.get("/usuarios/{usuario_id}/registros_habitos/", response_model=List[schemas.RegistroHabito])
def read_registros_habito_by_usuario(
    usuario_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    registros = crud.get_registros_habito_by_usuario(db=db, usuario_id=usuario_id, skip=skip, limit=limit)
    return registros


@router.get("/habitos/{habito_id}/registros/", response_model=List[schemas.RegistroHabito])
def read_registros_habito_by_habito(
    habito_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    db_habito = crud.get_habito(db, habito_id=habito_id)
    if db_habito is None:
        raise HTTPException(status_code=404, detail="Hábito no encontrado")
    registros = crud.get_registros_habito_by_habito(db=db, habito_id=habito_id, skip=skip, limit=limit)
    return registros
