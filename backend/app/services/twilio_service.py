"""
Servicio para integración con Twilio WhatsApp API.
Maneja el envío de mensajes a través de Twilio.
"""

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    Client = None
    
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

if not TWILIO_AVAILABLE:
    logger.warning("⚠️ Twilio package not installed. Install with: pip install twilio>=8.0.0")


class TwilioWhatsAppService:
    """Servicio para interactuar con la API de WhatsApp de Twilio."""
    
    def __init__(self):
        """Inicializa el cliente de Twilio."""
        if not TWILIO_AVAILABLE:
            logger.error("❌ Cannot initialize Twilio service: twilio package not installed")
            raise ImportError("twilio package is required. Install with: pip install twilio>=8.0.0")
            
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_WHATSAPP_NUMBER  # whatsapp:+14155238886
        
        if not self.account_sid or not self.auth_token:
            logger.warning("⚠️ Twilio credentials no configuradas")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("✅ Twilio WhatsApp client inicializado")
    
    def parse_webhook_message(self, body: dict) -> dict | None:
        """
        Parsea el mensaje entrante del webhook de Twilio.
        
        Args:
            body: Cuerpo del webhook de Twilio
            
        Returns:
            Dict con phone_number, message_text, message_id o None si no es válido
        """
        try:
            # Twilio usa una estructura más simple que Meta
            message_text = body.get('Body', '').strip()
            from_number = body.get('From', '')  # Formato: whatsapp:+5491165992142
            message_sid = body.get('MessageSid', '')
            
            if not message_text or not from_number:
                logger.warning("⚠️ Mensaje sin texto o remitente")
                return None
            
            # Extraer solo el número (remover "whatsapp:" prefix)
            phone_number = from_number.replace('whatsapp:', '').replace('+', '')
            
            logger.info(f"📱 Mensaje de Twilio parseado: {phone_number} -> {message_text}")
            
            return {
                'phone_number': phone_number,
                'message_text': message_text,
                'message_id': message_sid
            }
            
        except Exception as e:
            logger.error(f"❌ Error parseando mensaje de Twilio: {e}")
            return None
    
    async def send_message(self, phone_number: str, message: str) -> dict:
        """
        Envía un mensaje de WhatsApp usando Twilio.
        
        Args:
            phone_number: Número de teléfono del destinatario (sin whatsapp: prefix)
            message: Contenido del mensaje
            
        Returns:
            Dict con el resultado del envío
        """
        try:
            if not self.client:
                logger.error("❌ Cliente de Twilio no inicializado")
                return {'success': False, 'error': 'Twilio not configured'}
            
            # Asegurar formato whatsapp:+número
            to_number = f"whatsapp:+{phone_number}"
            
            print(f"📤 Enviando mensaje a WhatsApp (Twilio):")
            print(f"   From: {self.from_number}")
            print(f"   To: {to_number}")
            print(f"   Message: {message[:50]}...")
            
            # Enviar mensaje con Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            print(f"✅ Mensaje enviado exitosamente")
            print(f"   SID: {twilio_message.sid}")
            print(f"   Status: {twilio_message.status}")
            
            return {
                'success': True,
                'message_sid': twilio_message.sid,
                'status': twilio_message.status
            }
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje con Twilio: {e}")
            print(f"❌ Error enviando mensaje: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Instancia global del servicio
twilio_service = TwilioWhatsAppService()
