from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app import crud, schemas

router = APIRouter()


@router.post("/usuarios/", response_model=schemas.Usuario)
def create_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario_by_telefono(db, telefono=usuario.telefono)
    if db_usuario:
        raise HTTPException(status_code=400, detail="El teléfono ya está registrado")
    return crud.create_usuario(db=db, usuario=usuario)


@router.get("/usuarios/", response_model=List[schemas.Usuario])
def read_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    usuarios = crud.get_usuarios(db, skip=skip, limit=limit)
    return usuarios


@router.get("/usuarios/{usuario_id}", response_model=schemas.Usuario)
def read_usuario(usuario_id: int, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario


@router.post("/usuarios/{usuario_id}/estados_animo/", response_model=schemas.EstadoAnimo)
def create_estado_animo_for_usuario(
    usuario_id: int, estado_animo: schemas.EstadoAnimoCreate, db: Session = Depends(get_db)
):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return crud.create_estado_animo(db=db, estado_animo=estado_animo, usuario_id=usuario_id)


@router.get("/usuarios/{usuario_id}/estados_animo/", response_model=List[schemas.EstadoAnimo])
def read_estados_animo(usuario_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    estados_animo = crud.get_estados_animo_by_usuario(db=db, usuario_id=usuario_id, skip=skip, limit=limit)
    return estados_animo