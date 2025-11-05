"""
Tests for CRUD operations
"""
import pytest
from sqlalchemy.orm import Session
from app import crud, schemas
from app.models.mood import Usuario


def test_create_usuario(db_session: Session):
    """Test creating a new user"""
    usuario_data = schemas.UsuarioCreate(
        nombre="John Doe",
        telefono="+1234567890",
        timezone="America/New_York"
    )
    
    usuario = crud.create_usuario(db_session, usuario=usuario_data)
    
    assert usuario.id is not None
    assert usuario.nombre == "John Doe"
    assert usuario.telefono == "+1234567890"
    assert usuario.timezone == "America/New_York"
    assert usuario.nivel_confianza == 1  # Default


def test_get_usuario_by_telefono(db_session: Session, test_usuario: Usuario):
    """Test getting user by phone number"""
    usuario = crud.get_usuario_by_telefono(db_session, telefono=test_usuario.telefono)
    
    assert usuario is not None
    assert usuario.id == test_usuario.id
    assert usuario.telefono == test_usuario.telefono


def test_get_or_create_usuario_existing(db_session: Session, test_usuario: Usuario):
    """Test get_or_create with existing user"""
    usuario_data = schemas.UsuarioCreate(
        telefono=test_usuario.telefono,
        nombre="Different Name"
    )
    usuario = crud.get_or_create_usuario(db_session, usuario=usuario_data)
    
    # Should return existing user (not create a new one)
    assert usuario.id == test_usuario.id
    # Should keep original name
    assert usuario.nombre == test_usuario.nombre


def test_get_or_create_usuario_new(db_session: Session):
    """Test get_or_create with new user"""
    usuario_data = schemas.UsuarioCreate(
        telefono="+9999999999",
        nombre="New User"
    )
    usuario = crud.get_or_create_usuario(db_session, usuario=usuario_data)
    
    assert usuario.id is not None
    assert usuario.telefono == "+9999999999"
    assert usuario.nombre == "New User"


def test_create_habito(db_session: Session, test_usuario: Usuario):
    """Test creating a new habit"""
    habito_data = schemas.HabitoCreate(
        nombre_habito="Correr",
        categoria="ejercicio",
        objetivo_semanal=3,
        activo=True
    )
    
    habito = crud.create_habito(db_session, habito=habito_data, usuario_id=test_usuario.id)
    
    assert habito.id is not None
    assert habito.nombre_habito == "Correr"
    assert habito.categoria == "ejercicio"
    assert habito.usuario_id == test_usuario.id


def test_get_habitos_by_usuario(db_session: Session, test_usuario_with_habits: Usuario):
    """Test getting all habits for a user"""
    habitos = crud.get_habitos_by_usuario(db_session, usuario_id=test_usuario_with_habits.id)
    
    assert len(habitos) == 3
    habit_names = [h.nombre_habito for h in habitos]
    assert "Ejercicio" in habit_names
    assert "Meditar" in habit_names
    assert "Leer" in habit_names


def test_create_estado_animo(db_session: Session, test_usuario: Usuario):
    """Test creating a mood entry"""
    estado_data = schemas.EstadoAnimoCreate(
        nivel=7,
        notas_texto="Me siento bien hoy"
    )
    
    estado = crud.create_estado_animo(db_session, estado_animo=estado_data, usuario_id=test_usuario.id)
    
    assert estado.id is not None
    assert estado.nivel == 7
    assert estado.notas_texto == "Me siento bien hoy"
    assert estado.usuario_id == test_usuario.id


def test_create_conversacion(db_session: Session, test_usuario: Usuario):
    """Test creating a conversation entry"""
    conversacion_data = schemas.ConversacionContextoCreate(
        mensaje_usuario="Hola Loki",
        respuesta_loki="Hola! ¿Cómo estás?",
        entidades_extraidas='{"entities": []}',
        categorias_detectadas='["saludo"]'
    )
    
    conversacion = crud.create_conversacion(
        db_session,
        conversacion=conversacion_data,
        usuario_id=test_usuario.id
    )
    
    assert conversacion.id is not None
    assert conversacion.mensaje_usuario == "Hola Loki"
    assert conversacion.respuesta_loki == "Hola! ¿Cómo estás?"
    assert conversacion.usuario_id == test_usuario.id


def test_create_registro_habito(db_session: Session, test_usuario_with_habits: Usuario):
    """Test creating a habit tracking entry"""
    # Get one of the user's habits
    habitos = crud.get_habitos_by_usuario(db_session, usuario_id=test_usuario_with_habits.id)
    habito = habitos[0]
    
    registro_data = schemas.RegistroHabitoCreate(
        habito_id=habito.id,
        completado=True,
        notas="Completado hoy"
    )
    
    registro = crud.create_registro_habito(
        db_session,
        registro=registro_data,
        usuario_id=test_usuario_with_habits.id
    )
    
    assert registro.id is not None
    assert registro.habito_id == habito.id
    assert registro.completado is True
    assert registro.usuario_id == test_usuario_with_habits.id
