"""
Endpoints para registrar y obtener feedback de respuestas.
Sistema de mejora continua de Loki basado en feedback del usuario.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app import crud
from app.models.mood import FeedbackRespuesta, RespuestaExitosa, ConversacionContexto
from app.services.nlp_service import nlp_service

router = APIRouter()


class FeedbackSubmission(BaseModel):
    conversacion_id: int = None  # ID de la conversación si existe
    mensaje_usuario: str
    respuesta_loki: str
    utilidad_rating: int = None  # 1-5
    ayudo: bool = False
    notas: str = None


class RespuestaExitosaCreate(BaseModel):
    patron_pregunta: str
    respuesta_efectiva: str


@router.post("/api/v1/feedback/submit")
async def submit_feedback(
    usuario_id: int,
    feedback: FeedbackSubmission,
    db: Session = Depends(get_db)
):
    """
    Registra feedback sobre una respuesta de Loki.
    Usa el feedback para mejorar respuestas futuras.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        # Crear registro de feedback
        new_feedback = FeedbackRespuesta(
            usuario_id=usuario_id,
            conversacion_id=feedback.conversacion_id,
            mensaje_usuario=feedback.mensaje_usuario,
            respuesta_loki=feedback.respuesta_loki,
            utilidad_rating=feedback.utilidad_rating,
            ayudo=feedback.ayudo,
            notas_feedback=feedback.notas
        )

        db.add(new_feedback)

        # Si fue útil, registrar como respuesta exitosa
        if feedback.ayudo and feedback.utilidad_rating and feedback.utilidad_rating >= 4:
            # Detectar patrón de la pregunta usando NLP
            patron = _extract_question_pattern(feedback.mensaje_usuario)

            # Buscar si ya existe una respuesta exitosa similar
            existing = db.query(RespuestaExitosa).filter(
                and_(
                    RespuestaExitosa.usuario_id == usuario_id,
                    RespuestaExitosa.patron_pregunta == patron
                )
            ).first()

            if existing:
                # Actualizar existente
                existing.veces_usado += 1
                existing.utilidad_promedio = (
                    (existing.utilidad_promedio * (existing.veces_usado - 1) + feedback.utilidad_rating)
                    / existing.veces_usado
                )
                existing.fecha_ultima_uso = datetime.utcnow()
            else:
                # Crear nueva
                nueva_exitosa = RespuestaExitosa(
                    usuario_id=usuario_id,
                    patron_pregunta=patron,
                    respuesta_efectiva=feedback.respuesta_loki,
                    veces_usado=1,
                    utilidad_promedio=float(feedback.utilidad_rating)
                )
                db.add(nueva_exitosa)

        db.commit()

        return {
            'status': 'success',
            'mensaje': 'Feedback registrado correctamente',
            'feedback_id': new_feedback.id
        }

    except Exception as e:
        db.rollback()
        print(f"⚠️ Error registrando feedback: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al registrar feedback"
        )


@router.get("/api/v1/feedback/{usuario_id}/respuestas-exitosas")
async def get_respuestas_exitosas(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene las respuestas exitosas aprendidas para este usuario.
    Útil para mejorar prompting futuro.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        respuestas = db.query(RespuestaExitosa).filter(
            RespuestaExitosa.usuario_id == usuario_id
        ).order_by(RespuestaExitosa.utilidad_promedio.desc()).all()

        return {
            'usuario': usuario.nombre,
            'respuestas_exitosas': [
                {
                    'patron': r.patron_pregunta,
                    'respuesta': r.respuesta_efectiva,
                    'veces_usado': r.veces_usado,
                    'utilidad_promedio': round(r.utilidad_promedio, 2),
                    'fecha_descubierta': r.fecha_descubierta,
                    'fecha_ultima_uso': r.fecha_ultima_uso
                }
                for r in respuestas
            ],
            'total': len(respuestas)
        }
    except Exception as e:
        print(f"⚠️ Error obteniendo respuestas exitosas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener respuestas exitosas"
        )


@router.get("/api/v1/feedback/{usuario_id}/historial")
async def get_feedback_history(
    usuario_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de feedback del usuario.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        feedbacks = db.query(FeedbackRespuesta).filter(
            FeedbackRespuesta.usuario_id == usuario_id
        ).order_by(FeedbackRespuesta.timestamp.desc()).limit(limit).all()

        return {
            'usuario': usuario.nombre,
            'feedbacks': [
                {
                    'id': f.id,
                    'mensaje': f.mensaje_usuario,
                    'respuesta': f.respuesta_loki,
                    'rating': f.utilidad_rating,
                    'ayudo': f.ayudo,
                    'notas': f.notas_feedback,
                    'timestamp': f.timestamp
                }
                for f in feedbacks
            ],
            'total': len(feedbacks),
            'promedio_utilidad': _calculate_avg_rating(feedbacks)
        }
    except Exception as e:
        print(f"⚠️ Error obteniendo historial: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener historial de feedback"
        )


@router.get("/api/v1/feedback/{usuario_id}/estadisticas")
async def get_feedback_statistics(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de feedback del usuario.
    Helpful para entender qué funciona bien.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        feedbacks = db.query(FeedbackRespuesta).filter(
            FeedbackRespuesta.usuario_id == usuario_id
        ).all()

        if not feedbacks:
            return {
                'usuario': usuario.nombre,
                'total_feedback': 0,
                'mensaje': 'No hay feedback registrado aún'
            }

        total = len(feedbacks)
        ayudo = sum(1 for f in feedbacks if f.ayudo)
        rated = [f.utilidad_rating for f in feedbacks if f.utilidad_rating]

        avg_rating = sum(rated) / len(rated) if rated else 0
        success_rate = (ayudo / total * 100) if total > 0 else 0

        return {
            'usuario': usuario.nombre,
            'total_feedback': total,
            'respuestas_que_ayudaron': ayudo,
            'tasa_éxito': round(success_rate, 1),
            'rating_promedio': round(avg_rating, 2),
            'respuestas_exitosas_aprendidas': db.query(RespuestaExitosa).filter(
                RespuestaExitosa.usuario_id == usuario_id
            ).count()
        }
    except Exception as e:
        print(f"⚠️ Error calculando estadísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al calcular estadísticas"
        )


def _extract_question_pattern(mensaje: str) -> str:
    """
    Extrae un patrón simplificado de la pregunta/mensaje.
    Ej: "¿Cómo puedo manejar la ansiedad?" -> "ansiedad"
    """
    # Palabras clave de patrones
    pattern_keywords = {
        'ansiedad': ['ansiedad', 'ansioso', 'nervioso'],
        'tristeza': ['triste', 'deprimido', 'depresión'],
        'trabajo': ['trabajo', 'laboral', 'jefe'],
        'relaciones': ['pareja', 'familia', 'amigos'],
        'estrés': ['estrés', 'presión', 'agobiado'],
        'sueño': ['dormir', 'sueño', 'cansado'],
        'motivación': ['motivación', 'apatía', 'ganas'],
        'autoestima': ['autoestima', 'confianza', 'capaz'],
    }

    mensaje_lower = mensaje.lower()

    for pattern, keywords in pattern_keywords.items():
        if any(keyword in mensaje_lower for keyword in keywords):
            return pattern

    return 'general'


def _calculate_avg_rating(feedbacks: list) -> float:
    """Calcula rating promedio de una lista de feedbacks."""
    rated = [f.utilidad_rating for f in feedbacks if f.utilidad_rating]
    if not rated:
        return 0.0
    return round(sum(rated) / len(rated), 2)


# Import que faltaba
from sqlalchemy import and_
