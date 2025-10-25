"""
Servicio para integración con WhatsApp Business API.
Maneja webhooks entrantes y envío de mensajes.
"""

from typing import Dict, Any, Optional
import hmac
import hashlib
import httpx
from app.core.config import settings
from app.core.logger import setup_logger, log_security_event

logger = setup_logger(__name__)


class WhatsAppService:
    """
    Servicio para interactuar con WhatsApp Business API.
    """
    
    def __init__(self):
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica el webhook de WhatsApp durante la configuración inicial.
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verificado correctamente")
            return challenge
        log_security_event(logger, "webhook_verification_failed", f"mode={mode}", "WARNING")
        return None

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verifica la firma X-Hub-Signature-256 del webhook de Meta.

        Args:
            payload: Body del request como string
            signature: Header X-Hub-Signature-256

        Returns:
            True si la firma es válida, False si no
        """
        if not self.verify_token:
            logger.warning("WHATSAPP_VERIFY_TOKEN no configurado, no se puede verificar firma")
            return False

        if not signature:
            log_security_event(logger, "missing_webhook_signature", "No signature provided", "WARNING")
            return False

        # Calcular firma esperada
        expected_signature = "sha256=" + hmac.new(
            self.verify_token.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Comparación segura contra timing attacks
        is_valid = hmac.compare_digest(expected_signature, signature)

        if not is_valid:
            log_security_event(
                logger,
                "invalid_webhook_signature",
                "Firma inválida en webhook",
                "CRITICAL"
            )

        return is_valid
    
    def parse_webhook_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parsea el mensaje recibido del webhook de WhatsApp.

        Returns:
            Dict con 'phone_number', 'message_text', 'message_id', 'timestamp', 'profile_name'
            o None si no es un mensaje válido.
        """
        try:
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})

            # Verificar que hay mensajes
            messages = value.get('messages', [])
            if not messages:
                return None

            message = messages[0]

            # Solo procesar mensajes de texto por ahora
            if message.get('type') != 'text':
                return None

            # Extraer información del contacto si está disponible
            contacts = value.get('contacts', [])
            profile_name = None
            if contacts:
                profile = contacts[0].get('profile', {})
                profile_name = profile.get('name')

            return {
                'phone_number': message.get('from'),
                'message_text': message.get('text', {}).get('body', ''),
                'message_id': message.get('id'),
                'timestamp': message.get('timestamp'),
                'profile_name': profile_name  # Nombre del perfil de WhatsApp
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing webhook message: {e}")
            return None
    
    async def send_message(
        self, 
        phone_number: str, 
        message: str,
        phone_number_id: str = None
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de texto a través de WhatsApp Business API.
        
        Args:
            phone_number: Número de teléfono del destinatario (formato internacional)
            message: Texto del mensaje a enviar
            phone_number_id: ID del número de teléfono de WhatsApp Business
            
        Returns:
            Respuesta de la API de WhatsApp
        """
        if not self.access_token:
            logger.error("WhatsApp Access Token no configurado")
            return {"error": "WhatsApp not configured"}

        if not phone_number_id:
            # Este valor debe ser obtenido de la configuración de WhatsApp Business
            logger.error("Phone Number ID no configurado")
            return {"error": "Phone number ID not configured"}
        
        url = f"{self.base_url}/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        logger.info(f"Enviando mensaje WhatsApp a {phone_number}")
        logger.debug(f"Mensaje: {message[:100]}...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Mensaje enviado exitosamente a {phone_number}")
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            return {"error": str(e)}
    
    async def mark_message_as_read(
        self, 
        message_id: str,
        phone_number_id: str = None
    ) -> Dict[str, Any]:
        """
        Marca un mensaje como leído.
        """
        if not self.access_token or not phone_number_id:
            return {"error": "WhatsApp not configured"}
        
        url = f"{self.base_url}/{phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error marking message as read: {e}")
            return {"error": str(e)}


# Instancia singleton del servicio
whatsapp_service = WhatsAppService()
