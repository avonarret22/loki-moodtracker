"""
Endpoints para simular conversaciones con Loki.
Útil para testing sin necesidad de WhatsApp.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from app.db.session import get_db
from app import crud, schemas
from app.services.ai_service import loki_service

router = APIRouter()


class ChatMessage(BaseModel):
    usuario_id: int
    mensaje: str


class ChatResponse(BaseModel):
    respuesta: str
    contexto_extraido: dict
    mood_registrado: bool
    habitos_detectados: list


@router.post("/", response_model=ChatResponse)
async def chat_with_loki(chat_msg: ChatMessage, db: Session = Depends(get_db)):
    """
    Endpoint para chatear con Loki sin WhatsApp.
    Útil para testing y desarrollo.
    """
    print(f"\n{'='*60}")
    print(f"📨 Nuevo mensaje recibido de usuario {chat_msg.usuario_id}")
    print(f"📝 Mensaje: '{chat_msg.mensaje}'")
    print(f"{'='*60}\n")
    
    # Verificar que el usuario existe
    usuario = crud.get_usuario(db, usuario_id=chat_msg.usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener conversaciones recientes para contexto
    conversaciones_recientes = crud.get_conversaciones_by_usuario(
        db, usuario_id=usuario.id, limit=5
    )
    
    contexto_reciente = [
        {
            'mensaje_usuario': conv.mensaje_usuario,
            'respuesta_loki': conv.respuesta_loki
        }
        for conv in conversaciones_recientes
    ]
    
    # Generar respuesta con Loki AI (ahora con análisis de patrones)
    ai_response = await loki_service.generate_response(
        mensaje_usuario=chat_msg.mensaje,
        usuario_nombre=usuario.nombre,
        contexto_reciente=contexto_reciente,
        db_session=db,  # Pasar sesión de BD para análisis de patrones
        usuario_id=usuario.id  # Pasar ID de usuario
    )
    
    # Guardar la conversación
    conversacion_data = schemas.ConversacionContextoCreate(
        mensaje_usuario=chat_msg.mensaje,
        respuesta_loki=ai_response['respuesta'],
        entidades_extraidas=json.dumps(ai_response['context_extracted'], ensure_ascii=False),
        categorias_detectadas=json.dumps(ai_response['context_extracted'].get('habits_mentioned', []))
    )
    crud.create_conversacion(db, conversacion=conversacion_data, usuario_id=usuario.id)
    
    # Si se detectó un nivel de ánimo, registrarlo
    mood_registrado = False
    mood_level = ai_response['context_extracted'].get('mood_level')
    if mood_level:
        estado_animo_data = schemas.EstadoAnimoCreate(
            nivel=mood_level,
            notas_texto=chat_msg.mensaje,
            contexto_extraido=json.dumps(ai_response['context_extracted'], ensure_ascii=False),
            disparadores_detectados=json.dumps(
                ai_response['context_extracted'].get('emotional_triggers', [])
            )
        )
        crud.create_estado_animo(db, estado_animo=estado_animo_data, usuario_id=usuario.id)
        mood_registrado = True
    
    # Registrar hábitos mencionados
    habits_mentioned = ai_response['context_extracted'].get('habits_mentioned', [])
    for habit_name in habits_mentioned:
        # Buscar o crear el hábito
        existing_habits = crud.get_habitos_by_usuario(db, usuario_id=usuario.id)
        habit_exists = any(h.nombre_habito.lower() == habit_name.lower() for h in existing_habits)
        
        if not habit_exists:
            # Crear nuevo hábito
            from app.schemas import HabitoCreate
            habit_data = HabitoCreate(
                nombre_habito=habit_name,
                categoria=_categorize_habit(habit_name),
                objetivo_semanal=3
            )
            habit = crud.create_habito(db, habito=habit_data, usuario_id=usuario.id)
        else:
            # Encontrar el hábito existente
            habit = next(h for h in existing_habits if h.nombre_habito.lower() == habit_name.lower())
        
        # Registrar que el hábito fue mencionado/realizado hoy
        from app.schemas import RegistroHabitoCreate
        registro_data = RegistroHabitoCreate(
            habito_id=habit.id,
            completado=True,
            notas=f"Mencionado en conversación: {chat_msg.mensaje[:50]}..."
        )
        crud.create_registro_habito(db, registro=registro_data, usuario_id=usuario.id)
    
    return ChatResponse(
        respuesta=ai_response['respuesta'],
        contexto_extraido=ai_response['context_extracted'],
        mood_registrado=mood_registrado,
        habitos_detectados=habits_mentioned
    )


def _categorize_habit(habit_name: str) -> str:
    """Categoriza un hábito basado en su nombre."""
    habit_lower = habit_name.lower()
    
    if any(word in habit_lower for word in ['ejercicio', 'gym', 'correr', 'deporte', 'entrenar']):
        return 'ejercicio'
    elif any(word in habit_lower for word in ['dormir', 'sueño', 'descanso']):
        return 'sueño'
    elif any(word in habit_lower for word in ['social', 'amigos', 'familia', 'pareja']):
        return 'social'
    elif any(word in habit_lower for word in ['trabajo', 'proyecto', 'reunión']):
        return 'trabajo'
    elif any(word in habit_lower for word in ['meditar', 'mindfulness', 'respirar']):
        return 'mindfulness'
    elif any(word in habit_lower for word in ['comer', 'comida', 'alimentación']):
        return 'alimentación'
    else:
        return 'otro'


@router.get("/history/{usuario_id}")
async def get_chat_history(usuario_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """
    Obtiene el historial de conversaciones de un usuario.
    """
    usuario = crud.get_usuario(db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    conversaciones = crud.get_conversaciones_by_usuario(
        db, usuario_id=usuario_id, limit=limit
    )
    
    return {
        "usuario": usuario.nombre,
        "total_conversaciones": len(conversaciones),
        "conversaciones": [
            {
                "timestamp": conv.timestamp,
                "mensaje": conv.mensaje_usuario,
                "respuesta": conv.respuesta_loki,
                "contexto": json.loads(conv.entidades_extraidas) if conv.entidades_extraidas else {}
            }
            for conv in conversaciones
        ]
    }
