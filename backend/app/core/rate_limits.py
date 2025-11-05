"""
Configuración centralizada de rate limits para la API.
Define límites específicos para cada tipo de endpoint.
"""
from typing import Dict

# Rate limits por categoría de endpoint
RATE_LIMITS: Dict[str, str] = {
    # Endpoints públicos - muy restrictivos
    "public": "10/minute",
    
    # Endpoints de autenticación - moderados
    "auth": "5/minute",
    "auth_verify": "20/minute",
    
    # Webhooks de WhatsApp/Twilio - más generosos (tráfico legítimo)
    "whatsapp_webhook": "100/minute",
    "twilio_webhook": "100/minute",
    
    # Endpoints de chat/IA - controlados por usuario
    "chat": "30/minute",
    "ai_generation": "20/minute",
    
    # Endpoints de lectura - generosos
    "read": "60/minute",
    
    # Endpoints de escritura - moderados
    "write": "30/minute",
    
    # Endpoints de analytics - restrictivos (costosos)
    "analytics": "10/minute",
    
    # Dashboard - moderados
    "dashboard": "30/minute",
}


# Mensajes de error personalizados
RATE_LIMIT_MESSAGES: Dict[str, str] = {
    "public": "Demasiadas solicitudes. Por favor, espera un momento antes de intentar nuevamente.",
    "auth": "Demasiados intentos de autenticación. Por favor, espera 1 minuto.",
    "whatsapp_webhook": "Límite de mensajes alcanzado. Por favor, espera un momento.",
    "chat": "Estás enviando mensajes muy rápido. Por favor, espera un momento.",
    "analytics": "Demasiadas consultas de análisis. Por favor, espera un momento.",
    "default": "Límite de solicitudes alcanzado. Por favor, espera un momento.",
}


def get_rate_limit(category: str) -> str:
    """
    Obtiene el rate limit configurado para una categoría.
    
    Args:
        category: Categoría del endpoint (ej: 'auth', 'chat', 'whatsapp_webhook')
        
    Returns:
        String de rate limit en formato slowapi (ej: '10/minute')
    """
    return RATE_LIMITS.get(category, RATE_LIMITS["public"])


def get_rate_limit_message(category: str) -> str:
    """
    Obtiene el mensaje de error personalizado para una categoría.
    
    Args:
        category: Categoría del endpoint
        
    Returns:
        Mensaje de error amigable
    """
    return RATE_LIMIT_MESSAGES.get(category, RATE_LIMIT_MESSAGES["default"])


# Rate limits especiales por IP (whitelist/blacklist)
# Útil para permitir IPs de Meta/Twilio o bloquear atacantes
IP_WHITELIST = [
    # IPs de Meta/WhatsApp (agregar cuando se conozcan)
    # "157.240.0.0/16",  # Ejemplo
    # IPs de Twilio (agregar cuando se conozcan)
    # "54.172.60.0/23",  # Ejemplo
]

IP_BLACKLIST = [
    # IPs bloqueadas por abuso
    # Agregar dinámicamente cuando se detecten patrones de abuso
]
