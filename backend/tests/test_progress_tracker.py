"""
Tests para el servicio de detección de progresos.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.progress_tracker_service import (
    progress_tracker_service,
    ProgressInsight
)
from app.models.mood import Usuario, EstadoAnimo
from app import crud
from app.schemas.mood import UsuarioCreate, EstadoAnimoCreate


@pytest.fixture
def usuario_test(db_session: Session):
    """Crear usuario de prueba."""
    usuario = crud.create_usuario(
        db_session,
        UsuarioCreate(
            nombre="Test User",
            telefono="+1234567890",
            timezone="UTC"
        )
    )
    yield usuario
    # Cleanup
    db_session.query(EstadoAnimo).filter(EstadoAnimo.usuario_id == usuario.id).delete()
    db_session.query(Usuario).filter(Usuario.id == usuario.id).delete()
    db_session.commit()


class TestProgressTrackerService:
    """Tests para el servicio de seguimiento de progreso."""
    
    def test_detect_mood_improvement(self, db_session: Session, usuario_test):
        """Debe detectar mejora en el mood promedio."""
        ahora = datetime.utcnow()
        
        # Crear moods de hace 14 días (promedio 4)
        for i in range(7):
            fecha = ahora - timedelta(days=14-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=4, notas_texto="Test mood bajo"),
                usuario_id=usuario_test.id
            )
            # Actualizar timestamp manualmente
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # Crear moods recientes (promedio 7)
        for i in range(7):
            fecha = ahora - timedelta(days=6-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=7, notas_texto="Test mood alto"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # Detectar progreso
        insight = progress_tracker_service._detect_mood_improvement(
            db_session,
            usuario_test.id
        )
        
        assert insight is not None
        assert insight.tipo == 'mejoria_promedio'
        assert insight.datos['mejora'] >= 2.0  # Mejora significativa
        assert insight.nivel_significancia >= 7
    
    def test_detect_positive_streak(self, db_session: Session, usuario_test):
        """Debe detectar racha de días consecutivos positivos."""
        ahora = datetime.utcnow()
        
        # Crear 5 días consecutivos con mood >= 7
        for i in range(5):
            fecha = ahora - timedelta(days=4-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=8, notas_texto="Día positivo"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # Detectar racha
        insight = progress_tracker_service._detect_positive_streak(
            db_session,
            usuario_test.id
        )
        
        assert insight is not None
        assert insight.tipo == 'racha_positiva'
        assert insight.datos['dias_racha'] >= 3
        assert insight.datos['threshold'] == 7
    
    def test_detect_overcome_difficulty(self, db_session: Session, usuario_test):
        """Debe detectar superación de momento difícil."""
        ahora = datetime.utcnow()
        
        # Crear patrón: bajo (3) → medio (5) → alto (8)
        # Período 1: bajo
        for i in range(3):
            fecha = ahora - timedelta(days=9-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=3, notas_texto="Momento difícil"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # Período 2: medio
        for i in range(3):
            fecha = ahora - timedelta(days=6-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=5, notas_texto="Mejorando"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # Período 3: alto
        for i in range(3):
            fecha = ahora - timedelta(days=2-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=8, notas_texto="Recuperado"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # Detectar superación
        insight = progress_tracker_service._detect_overcome_difficulty(
            db_session,
            usuario_test.id
        )
        
        assert insight is not None
        assert insight.tipo == 'superacion_momento_dificil'
        assert insight.datos['mood_inicial'] <= 4
        assert insight.datos['mood_actual'] >= 7
        assert insight.datos['mejora_total'] >= 3
    
    def test_get_progress_insights_prioritization(self, db_session: Session, usuario_test):
        """Debe priorizar el insight más significativo."""
        ahora = datetime.utcnow()
        
        # Crear datos que generen múltiples insights
        # 1. Mejora de mood
        for i in range(7):
            fecha = ahora - timedelta(days=14-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=4, notas_texto="Antes"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # 2. Racha positiva reciente
        for i in range(5):
            fecha = ahora - timedelta(days=4-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=9, notas_texto="Racha"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # Obtener insight principal
        insight = progress_tracker_service.get_progress_insights(
            db_session,
            usuario_test.id
        )
        
        assert insight is not None
        # Debe retornar el de mayor significancia
        assert insight.nivel_significancia >= 6
    
    def test_no_progress_when_insufficient_data(self, db_session: Session, usuario_test):
        """No debe detectar progreso con datos insuficientes."""
        # Solo crear 2 moods
        crud.create_estado_animo(
            db_session,
            EstadoAnimoCreate(nivel=5, notas_texto="Test 1"),
            usuario_id=usuario_test.id
        )
        crud.create_estado_animo(
            db_session,
            EstadoAnimoCreate(nivel=7, notas_texto="Test 2"),
            usuario_id=usuario_test.id
        )
        
        insight = progress_tracker_service.get_progress_insights(
            db_session,
            usuario_test.id
        )
        
        # Puede ser None o tener baja significancia
        assert insight is None or insight.nivel_significancia < 5
    
    def test_generate_celebration_context_low_trust(self, db_session: Session, usuario_test):
        """Debe generar contexto sutil para nivel de confianza bajo."""
        insight = ProgressInsight(
            tipo='mejoria_promedio',
            mensaje_contexto="Test mejora",
            datos={'mejora': 2.0},
            nivel_significancia=7
        )
        
        context = progress_tracker_service.generate_celebration_context(
            insight,
            nivel_confianza=2
        )
        
        assert isinstance(context, str)
        assert len(context) > 0
        # Debe ser sutil
        assert "Nota:" in context
        # Debe tener advertencia anti-cursilería
        assert "IMPORTANTE" in context
        assert "NO uses" in context or "orgulloso" in context
    
    def test_generate_celebration_context_high_trust(self, db_session: Session, usuario_test):
        """Debe generar contexto más directo para nivel de confianza alto."""
        insight = ProgressInsight(
            tipo='racha_positiva',
            mensaje_contexto="Test racha",
            datos={'dias_racha': 5, 'threshold': 7},
            nivel_significancia=9
        )
        
        context = progress_tracker_service.generate_celebration_context(
            insight,
            nivel_confianza=4
        )
        
        assert isinstance(context, str)
        assert len(context) > 0
        # Debe ser más directo
        assert "RACHA POSITIVA" in context or "racha" in context.lower()
        # Debe mantener advertencia
        assert "IMPORTANTE" in context
    
    def test_no_progress_when_mood_decreases(self, db_session: Session, usuario_test):
        """No debe detectar progreso si el mood ha empeorado."""
        ahora = datetime.utcnow()
        
        # Crear moods que empeoran
        for i in range(7):
            fecha = ahora - timedelta(days=14-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=8, notas_texto="Antes alto"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        for i in range(7):
            fecha = ahora - timedelta(days=6-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=4, notas_texto="Ahora bajo"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        insight = progress_tracker_service._detect_mood_improvement(
            db_session,
            usuario_test.id
        )
        
        # No debe detectar mejora (el mood empeoró)
        assert insight is None
    
    def test_streak_breaks_on_low_mood(self, db_session: Session, usuario_test):
        """La racha debe romperse cuando hay un día con mood bajo."""
        ahora = datetime.utcnow()
        
        # 3 días buenos
        for i in range(3):
            fecha = ahora - timedelta(days=4-i)
            crud.create_estado_animo(
                db_session,
                EstadoAnimoCreate(nivel=8, notas_texto="Bien"),
                usuario_id=usuario_test.id
            )
            ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
            ultimo.timestamp = fecha
            db_session.commit()
        
        # 1 día malo (rompe la racha)
        fecha = ahora - timedelta(days=1)
        crud.create_estado_animo(
            db_session,
            EstadoAnimoCreate(nivel=3, notas_texto="Mal día"),
            usuario_id=usuario_test.id
        )
        ultimo = db_session.query(EstadoAnimo).order_by(EstadoAnimo.id.desc()).first()
        ultimo.timestamp = fecha
        db_session.commit()
        
        # 1 día bueno reciente (no cuenta como racha larga)
        crud.create_estado_animo(
            db_session,
            EstadoAnimoCreate(nivel=8, notas_texto="Hoy bien"),
            usuario_id=usuario_test.id
        )
        
        insight = progress_tracker_service._detect_positive_streak(
            db_session,
            usuario_test.id
        )
        
        # La racha se rompió, solo cuenta el último día
        if insight:
            assert insight.datos['dias_racha'] < 3
