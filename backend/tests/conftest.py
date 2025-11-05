"""
Pytest configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.db.session import Base
from app.models.mood import Usuario
from app import schemas, crud


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Create a fresh database session for each test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_usuario(db_session: Session) -> Usuario:
    """
    Create a test user for testing.
    """
    usuario_data = schemas.UsuarioCreate(
        nombre="Test User",
        telefono="+1234567890",
        timezone="UTC"
    )
    
    usuario = crud.create_usuario(db_session, usuario=usuario_data)
    return usuario


@pytest.fixture(scope="function")
def test_usuario_with_habits(db_session: Session, test_usuario: Usuario):
    """
    Create a test user with some habits.
    """
    # Create some habits
    habits = [
        schemas.HabitoCreate(
            nombre_habito="Ejercicio",
            categoria="ejercicio",
            objetivo_semanal=5,
            activo=True
        ),
        schemas.HabitoCreate(
            nombre_habito="Meditar",
            categoria="mindfulness",
            objetivo_semanal=7,
            activo=True
        ),
        schemas.HabitoCreate(
            nombre_habito="Leer",
            categoria="hobbies",
            objetivo_semanal=3,
            activo=True
        ),
    ]
    
    for habit_data in habits:
        crud.create_habito(db_session, habito=habit_data, usuario_id=test_usuario.id)
    
    return test_usuario
