"""
Endpoints para el webhook de Twilio WhatsApp.
Recibe mensajes entrantes y responde con la IA de Loki.
"""

from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
import json

from app.db.session import get_db
from app import crud, schemas
from app.services.twilio_service import twilio_service
from app.services.ai_service import loki_service

router = APIRouter()


@router.post("/webhook")
async def receive_twilio_webhook(
    request: Request,
    db: Session = Depends(get_db),
    Body: str = Form(None),
    From: str = Form(None),
    MessageSid: str = Form(None)
):
    """
    Endpoint para recibir mensajes entrantes de Twilio WhatsApp.
    Procesa el mensaje con Loki AI y responde al usuario.
    
    Twilio envía datos como form-data, no JSON.
    """
    
    # Verificar que Twilio service esté disponible
    if twilio_service is None:
        print("❌ Twilio service not available - twilio package not installed")
        return {"status": "error", "message": "Twilio service not configured"}
    
    try:
        # Construir body dict desde form data
        body = {
            'Body': Body,
            'From': From,
            'MessageSid': MessageSid
        }
        
        print(f"📥 Webhook de Twilio recibido:")
        print(f"   From: {From}")
        print(f"   Message: {Body}")
        print(f"   SID: {MessageSid}")
        
        # Parsear el mensaje
        parsed_message = twilio_service.parse_webhook_message(body)
        
        if not parsed_message:
            # No es un mensaje de texto válido, ignorar
            print("⚠️ No es un mensaje de texto válido, ignorando")
            return {"status": "ok"}
        
        phone_number = parsed_message['phone_number']
        message_text = parsed_message['message_text']
        message_id = parsed_message['message_id']
        
        print(f"📱 Mensaje parseado:")
        print(f"   Número: {phone_number}")
        print(f"   Texto: {message_text}")
        print(f"   ID: {message_id}")
        
        # Buscar o crear usuario basado en el número de teléfono
        usuario = crud.get_usuario_by_telefono(db, telefono=phone_number)
        
        if not usuario:
            # Crear nuevo usuario si es la primera vez que escribe
            usuario_data = schemas.UsuarioCreate(
                nombre=f"Usuario {phone_number[-4:]}",  # Nombre temporal
                telefono=phone_number
            )
            usuario = crud.create_usuario(db, usuario=usuario_data)
        
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
        
        # Generar respuesta con Loki AI
        ai_response = await loki_service.generate_response(
            mensaje_usuario=message_text,
            usuario_nombre=usuario.nombre,
            contexto_reciente=contexto_reciente
        )
        
        # Guardar la conversación
        conversacion_data = schemas.ConversacionContextoCreate(
            mensaje_usuario=message_text,
            respuesta_loki=ai_response['respuesta'],
            entidades_extraidas=json.dumps(ai_response['context_extracted'], ensure_ascii=False),
            categorias_detectadas=json.dumps(ai_response['context_extracted'].get('habits_mentioned', []))
        )
        crud.create_conversacion(db, conversacion=conversacion_data, usuario_id=usuario.id)
        
        # Si se detectó un nivel de ánimo, registrarlo
        mood_level = ai_response['context_extracted'].get('mood_level')
        if mood_level:
            estado_animo_data = schemas.EstadoAnimoCreate(
                nivel=mood_level,
                notas_texto=message_text,
                contexto_extraido=json.dumps(ai_response['context_extracted'], ensure_ascii=False),
                disparadores_detectados=json.dumps(
                    ai_response['context_extracted'].get('emotional_triggers', [])
                )
            )
            crud.create_estado_animo(db, estado_animo=estado_animo_data, usuario_id=usuario.id)
        
        # Si se detectaron hábitos, registrarlos
        habits_mentioned = ai_response['context_extracted'].get('habits_mentioned', [])
        if habits_mentioned:
            # TODO: Implementar lógica para crear/actualizar hábitos automáticamente
            pass
        
        # Enviar respuesta por WhatsApp usando Twilio
        result = await twilio_service.send_message(
            phone_number=phone_number,
            message=ai_response['respuesta']
        )
        
        if result.get('success'):
            print(f"✅ Mensaje enviado a {phone_number}: {ai_response['respuesta']}")
        else:
            print(f"❌ Error enviando mensaje: {result.get('error')}")
        
        return {"status": "ok", "message": "processed"}
        
    except Exception as e:
        print(f"❌ Error processing Twilio webhook: {e}")
        import traceback
        traceback.print_exc()
        # Twilio espera un 200 OK incluso si hay errores
        return {"status": "error", "message": str(e)}
