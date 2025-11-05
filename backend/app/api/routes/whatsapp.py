"""
Endpoints para el webhook de WhatsApp.
Recibe mensajes entrantes y responde con la IA de Loki.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import json

from app.db.session import get_db
from app import crud, schemas
from app.services.whatsapp_service import whatsapp_service
from app.services.ai_service import loki_service
from app.services.trust_level_service import trust_service
from app.core.logger import setup_logger, log_security_event

logger = setup_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


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
@limiter.limit("100/minute")  # Máximo 100 requests por minuto por IP
async def receive_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para recibir mensajes entrantes de WhatsApp.
    Procesa el mensaje con Loki AI y responde al usuario.
    """
    try:
        # Verificar firma del webhook (seguridad)
        signature = request.headers.get("X-Hub-Signature-256")
        body_bytes = await request.body()
        body_str = body_bytes.decode()

        # Validar firma si está configurada
        if signature:
            is_valid = whatsapp_service.verify_webhook_signature(body_str, signature)
            if not is_valid:
                log_security_event(
                    logger,
                    "invalid_webhook_signature",
                    "Intento de acceso con firma inválida",
                    "CRITICAL"
                )
                raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning("Webhook recibido sin firma X-Hub-Signature-256")

        # Parsear JSON del body
        body = json.loads(body_str)

        logger.info("Webhook recibido de WhatsApp")
        logger.debug(f"Body: {json.dumps(body, indent=2, ensure_ascii=False)}")
        
        # Parsear el mensaje
        parsed_message = whatsapp_service.parse_webhook_message(body)


        if not parsed_message:
            # No es un mensaje de texto válido, ignorar
            logger.info("Mensaje no es de texto válido, ignorando")
            return {"status": "ok"}

        phone_number = parsed_message['phone_number']
        message_text = parsed_message['message_text']
        message_id = parsed_message['message_id']
        profile_name = parsed_message.get('profile_name')

        logger.info(f"Mensaje recibido de {phone_number} (ID: {message_id})")
        logger.debug(f"Contenido: {message_text}")
        if profile_name:
            logger.debug(f"Nombre del perfil: {profile_name}")

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
            logger.info(f"Nuevo usuario creado: {nombre_usuario} ({phone_number})")
        elif profile_name and usuario.nombre != profile_name and usuario.nombre.startswith("Usuario"):
            # Actualizar nombre si tenemos el nombre del perfil y el actual es temporal
            usuario.nombre = profile_name
            db.commit()
            db.refresh(usuario)
            logger.info(f"Nombre de usuario actualizado a: {profile_name}")
        
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
            logger.info(f"Nivel de confianza aumentó para usuario {usuario.id}: {trust_update['nivel_info']['name']}")

        # Generar respuesta con Loki AI
        ai_response = await loki_service.generate_response(
            mensaje_usuario=message_text,
            usuario_nombre=usuario.nombre,
            contexto_reciente=contexto_reciente,
            db_session=db,
            usuario_id=usuario.id
        )
        
        # 🆕 Si se detectó un nombre, actualizarlo en la BD
        nombre_detectado = ai_response.get('nombre_detectado')
        if nombre_detectado:
            usuario.nombre = nombre_detectado
            db.commit()
            db.refresh(usuario)
            logger.info(f"✅ Nombre actualizado a: {nombre_detectado} para usuario {usuario.id}")
        
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
        
        # Si se detectaron hábitos, registrarlos automáticamente
        habits_mentioned = ai_response['context_extracted'].get('habits_mentioned', [])
        if habits_mentioned:
            from app.services.habit_automation import create_or_update_habits_from_mentions, get_habit_summary
            
            try:
                habits_result = await create_or_update_habits_from_mentions(
                    db=db,
                    usuario_id=usuario.id,
                    habits_mentioned=habits_mentioned
                )
                
                # Log del resultado
                summary = get_habit_summary(habits_result)
                if summary:
                    logger.info(f"Hábitos auto-gestionados para {phone_number}: {summary}")
                    
            except Exception as e:
                logger.error(f"Error auto-gestionando hábitos: {e}")
                # No fallar el flujo principal si hay error en hábitos
        
        # Enviar respuesta por WhatsApp
        await whatsapp_service.send_message(
            phone_number=phone_number,
            message=ai_response['respuesta'],
            phone_number_id=whatsapp_service.phone_number_id
        )

        logger.info(f"Respuesta enviada a {phone_number}")
        logger.debug(f"Respuesta: {ai_response['respuesta'][:100]}...")

        return {"status": "ok", "message": "processed"}

    except HTTPException:
        # Re-raise HTTPException para validación de firma
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
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
