"""
Endpoints para el webhook de WhatsApp.
Recibe mensajes entrantes y responde con la IA de Loki.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import json

from app.db.session import get_db
from app import crud, schemas
from app.services.whatsapp_service import whatsapp_service
from app.services.ai_service import loki_service
from app.services.trust_level_service import trust_service

router = APIRouter()


@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    """
    Endpoint para verificar el webhook de WhatsApp.
    WhatsApp llama a este endpoint durante la configuración inicial.
    """
    verified_challenge = whatsapp_service.verify_webhook(mode, token, challenge)
    
    if verified_challenge:
        return int(verified_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para recibir mensajes entrantes de WhatsApp.
    Procesa el mensaje con Loki AI y responde al usuario.
    """
    try:
        # Obtener el cuerpo del webhook
        body = await request.json()
        
        print(f"📥 Webhook recibido:")
        print(f"   Body completo: {json.dumps(body, indent=2, ensure_ascii=False)}")
        
        # Parsear el mensaje
        parsed_message = whatsapp_service.parse_webhook_message(body)
        
        if not parsed_message:
            # No es un mensaje de texto válido, ignorar
            print("⚠️ No es un mensaje de texto válido, ignorando")
            return {"status": "ok"}
        
        phone_number = parsed_message['phone_number']
        message_text = parsed_message['message_text']
        message_id = parsed_message['message_id']
        profile_name = parsed_message.get('profile_name')

        print(f"📱 Mensaje parseado:")
        print(f"   Número: {phone_number}")
        print(f"   Nombre: {profile_name or 'No disponible'}")
        print(f"   Texto: {message_text}")
        print(f"   ID: {message_id}")

        # Buscar o crear usuario basado en el número de teléfono
        usuario = crud.get_usuario_by_telefono(db, telefono=phone_number)

        if not usuario:
            # Crear nuevo usuario si es la primera vez que escribe
            # Usar nombre del perfil de WhatsApp si está disponible
            nombre_usuario = profile_name if profile_name else "Usuario de WhatsApp"

            usuario_data = schemas.UsuarioCreate(
                nombre=nombre_usuario,
                telefono=phone_number
            )
            usuario = crud.create_usuario(db, usuario=usuario_data)
            print(f"✅ Nuevo usuario creado: {nombre_usuario} ({phone_number})")
        elif profile_name and usuario.nombre != profile_name and usuario.nombre.startswith("Usuario"):
            # Actualizar nombre si tenemos el nombre del perfil y el actual es temporal
            usuario.nombre = profile_name
            db.commit()
            db.refresh(usuario)
            print(f"✅ Nombre de usuario actualizado a: {profile_name}")
        
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

        # Actualizar nivel de confianza (incrementa contador de interacciones)
        trust_update = trust_service.update_trust_level(db, usuario.id)
        if trust_update.get('nivel_cambio'):
            print(f"🎉 ¡Nivel de confianza aumentó! Ahora: {trust_update['nivel_info']['name']}")

        # Generar respuesta con Loki AI
        ai_response = await loki_service.generate_response(
            mensaje_usuario=message_text,
            usuario_nombre=usuario.nombre,
            contexto_reciente=contexto_reciente,
            db_session=db,
            usuario_id=usuario.id
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
        
        # Si se detectaron hábitos, registrarlos (opcional: crear/actualizar hábitos automáticamente)
        habits_mentioned = ai_response['context_extracted'].get('habits_mentioned', [])
        if habits_mentioned:
            # TODO: Implementar lógica para crear/actualizar hábitos automáticamente
            pass
        
        # Enviar respuesta por WhatsApp
        await whatsapp_service.send_message(
            phone_number=phone_number,
            message=ai_response['respuesta'],
            phone_number_id=whatsapp_service.phone_number_id
        )
        
        print(f"Mensaje enviado a {phone_number}: {ai_response['respuesta']}")
        
        return {"status": "ok", "message": "processed"}
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        # WhatsApp espera un 200 OK incluso si hay errores
        return {"status": "error", "message": str(e)}


@router.post("/send-test-message")
async def send_test_message(
    phone_number: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    Endpoint de prueba para enviar mensajes manualmente.
    """
    # TODO: Implementar con phone_number_id real
    result = await whatsapp_service.send_message(
        phone_number=phone_number,
        message=message
    )
    
    return result
