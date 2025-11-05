"""
Utilidades de sanitización y validación de inputs para prevenir inyecciones y XSS.
"""
import re
import html
from typing import Optional


# Patrones peligrosos comunes
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Scripts
    r'javascript:',  # JavaScript protocol
    r'on\w+\s*=',  # Event handlers (onclick, onload, etc)
    r'<iframe[^>]*>',  # IFrames
    r'<embed[^>]*>',  # Embeds
    r'<object[^>]*>',  # Objects
]


def sanitize_html(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitiza texto HTML escapando caracteres peligrosos.
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima opcional
        
    Returns:
        Texto sanitizado
        
    Example:
        >>> sanitize_html("<script>alert('xss')</script>Hello")
        "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;Hello"
    """
    if not text:
        return ""
    
    # Escapar HTML
    text = html.escape(text)
    
    # Aplicar límite de longitud si se especifica
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def sanitize_phone_number(phone: str) -> str:
    """
    Sanitiza y normaliza números de teléfono.
    
    Args:
        phone: Número de teléfono a sanitizar
        
    Returns:
        Número sanitizado (solo dígitos y +)
        
    Example:
        >>> sanitize_phone_number("+1 (555) 123-4567")
        "+15551234567"
    """
    if not phone:
        return ""
    
    # Remover prefijo whatsapp: si existe
    phone = phone.replace("whatsapp:", "")
    
    # Mantener solo dígitos y +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Asegurar que empieza con +
    if not phone.startswith('+'):
        phone = '+' + phone
    
    return phone


def sanitize_json_string(text: str) -> str:
    """
    Sanitiza strings que serán almacenados como JSON.
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto sanitizado sin caracteres de control
    """
    if not text:
        return ""
    
    # Remover caracteres de control excepto newlines y tabs
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Escapar comillas dobles para JSON
    text = text.replace('"', '\\"')
    
    return text.strip()


def validate_no_sql_injection(text: str) -> bool:
    """
    Verifica que el texto no contenga patrones de SQL injection.
    
    Args:
        text: Texto a validar
        
    Returns:
        True si es seguro, False si contiene patrones sospechosos
        
    Note:
        Esta es una capa adicional de seguridad. SQLAlchemy con parámetros
        preparados ya previene SQL injection.
    """
    if not text:
        return True
    
    # Patrones sospechosos de SQL injection
    sql_patterns = [
        r"(\bOR\b|\bAND\b)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",  # OR 1=1
        r";\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)\s+",  # Comandos SQL
        r"--",  # Comentarios SQL
        r"/\*.*\*/",  # Comentarios multilinea
        r"UNION\s+SELECT",  # UNION attacks
        r"exec\s*\(",  # Ejecución de comandos
    ]
    
    text_upper = text.upper()
    for pattern in sql_patterns:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return False
    
    return True


def validate_no_xss(text: str) -> bool:
    """
    Verifica que el texto no contenga patrones de XSS.
    
    Args:
        text: Texto a validar
        
    Returns:
        True si es seguro, False si contiene patrones peligrosos
    """
    if not text:
        return True
    
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            return False
    
    return True


def sanitize_user_input(
    text: str,
    max_length: int = 5000,
    allow_html: bool = False,
    check_sql: bool = True,
    check_xss: bool = True
) -> str:
    """
    Sanitización completa de input de usuario.
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
        allow_html: Si False, escapa todo el HTML
        check_sql: Si True, valida contra SQL injection
        check_xss: Si True, valida contra XSS
        
    Returns:
        Texto sanitizado
        
    Raises:
        ValueError: Si el texto contiene patrones peligrosos
    """
    if not text:
        return ""
    
    # Validar contra SQL injection
    if check_sql and not validate_no_sql_injection(text):
        raise ValueError("Texto contiene patrones sospechosos de SQL injection")
    
    # Validar contra XSS
    if check_xss and not validate_no_xss(text):
        raise ValueError("Texto contiene patrones sospechosos de XSS")
    
    # Sanitizar HTML si no se permite
    if not allow_html:
        text = sanitize_html(text, max_length)
    else:
        # Aplicar límite de longitud
        if len(text) > max_length:
            text = text[:max_length]
    
    return text.strip()


def validate_email(email: str) -> bool:
    """
    Valida formato de email básico.
    
    Args:
        email: Email a validar
        
    Returns:
        True si el formato es válido
    """
    if not email:
        return False
    
    # Patrón básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Valida formato de URL básico.
    
    Args:
        url: URL a validar
        
    Returns:
        True si el formato es válido
    """
    if not url:
        return False
    
    # Patrón básico de URL (http/https)
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url))
