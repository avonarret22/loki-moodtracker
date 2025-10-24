"""
Endpoints para obtener recomendaciones proactivas e inteligentes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app import crud
from app.services.recommendation_service import recommendation_service
from app.services.emotion_analysis_service import emotion_service

router = APIRouter()


@router.get("/api/v1/recommendations/{usuario_id}")
async def get_personalized_recommendations(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene recomendaciones proactivas personalizadas para el usuario.
    Incluye: hábitos preventivos, desafíos, micro-hábitos y próxima acción recomendada.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Obtener ánimo actual (el más reciente)
    recent_mood = db.query(EstadoAnimo).filter(
        EstadoAnimo.usuario_id == usuario_id
    ).order_by(EstadoAnimo.timestamp.desc()).first()

    current_mood = recent_mood.nivel if recent_mood else None

    try:
        # Generar todas las recomendaciones
        preventivas = recommendation_service.suggest_preventive_activities(db, usuario_id)
        desafios = recommendation_service.generate_personalized_challenges(
            db, usuario_id, difficulty='moderate'
        )
        micro_habitos = recommendation_service.suggest_micro_habits(current_mood)
        next_action = recommendation_service.get_next_recommended_action(db, usuario_id, current_mood)

        return {
            'usuario': usuario.nombre,
            'current_mood': current_mood,
            'recomendaciones': {
                'preventivas': preventivas,
                'desafios': desafios,
                'micro_habitos': micro_habitos,
                'proxima_accion': next_action
            },
            'fecha_generacion': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"⚠️ Error generando recomendaciones: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al generar recomendaciones"
        )


@router.get("/api/v1/recommendations/{usuario_id}/emotional-cycles")
async def get_emotional_cycles(
    usuario_id: int,
    days_lookback: int = 90,
    db: Session = Depends(get_db)
):
    """
    Obtiene análisis de ciclos emocionales del usuario.
    Detecta patrones diarios, semanales y mensuales.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        cycles = emotion_service.detect_emotional_cycles(
            db, usuario_id, days_lookback=days_lookback
        )

        if 'error' in cycles:
            raise HTTPException(
                status_code=400,
                detail=cycles['error']
            )

        return {
            'usuario': usuario.nombre,
            'ciclos_emocionales': cycles
        }
    except Exception as e:
        print(f"⚠️ Error analizando ciclos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al analizar ciclos emocionales"
        )


@router.get("/api/v1/recommendations/{usuario_id}/challenges")
async def get_challenges(
    usuario_id: int,
    difficulty: str = 'moderate',
    db: Session = Depends(get_db)
):
    """
    Obtiene desafíos personalizados del usuario.

    Parámetros:
        difficulty: 'easy'|'moderate'|'hard'
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if difficulty not in ['easy', 'moderate', 'hard']:
        difficulty = 'moderate'

    try:
        challenges = recommendation_service.generate_personalized_challenges(
            db, usuario_id, difficulty=difficulty
        )

        return {
            'usuario': usuario.nombre,
            'dificultad': difficulty,
            'desafios': challenges
        }
    except Exception as e:
        print(f"⚠️ Error generando desafíos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al generar desafíos"
        )


@router.get("/api/v1/recommendations/{usuario_id}/micro-habits")
async def get_micro_habits(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene micro-hábitos recomendados (acciones de 1-5 minutos).
    Se adaptan al ánimo actual del usuario.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        # Obtener ánimo actual
        from app.models.mood import EstadoAnimo
        recent_mood = db.query(EstadoAnimo).filter(
            EstadoAnimo.usuario_id == usuario_id
        ).order_by(EstadoAnimo.timestamp.desc()).first()

        current_mood = recent_mood.nivel if recent_mood else None

        micro_habitos = recommendation_service.suggest_micro_habits(current_mood)

        return {
            'usuario': usuario.nombre,
            'ánimo_actual': current_mood,
            'micro_habitos': micro_habitos
        }
    except Exception as e:
        print(f"⚠️ Error obteniendo micro-hábitos: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener micro-hábitos"
        )


@router.get("/api/v1/recommendations/{usuario_id}/next-action")
async def get_next_action(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la próxima acción más relevante recomendada.
    La acción más apropiada según el contexto actual.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        from app.models.mood import EstadoAnimo
        recent_mood = db.query(EstadoAnimo).filter(
            EstadoAnimo.usuario_id == usuario_id
        ).order_by(EstadoAnimo.timestamp.desc()).first()

        current_mood = recent_mood.nivel if recent_mood else None

        next_action = recommendation_service.get_next_recommended_action(
            db, usuario_id, current_mood
        )

        if not next_action:
            return {
                'usuario': usuario.nombre,
                'próxima_acción': None,
                'mensaje': 'No hay acciones recomendadas en este momento'
            }

        return {
            'usuario': usuario.nombre,
            'próxima_acción': next_action,
            'fecha': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"⚠️ Error obteniendo próxima acción: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener próxima acción"
        )


# Imports que faltaban
from datetime import datetime
from app.models.mood import EstadoAnimo
