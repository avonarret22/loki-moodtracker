"""
Servicio de autenticación con JWT para dashboard.
Genera tokens seguros para acceso al dashboard sin password.
"""
import jwt
import datetime
from typing import Optional, Dict

from app.core.config import settings
from app.core.logger import setup_logger, log_security_event

logger = setup_logger(__name__)

# Secret key para JWT - REQUERIDO en variables de entorno
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 24


class AuthService:
    """Servicio para generar y verificar tokens de autenticación."""
    
    @staticmethod
    def generate_dashboard_token(usuario_id: int, telefono: str) -> str:
        """
        Genera un token JWT para acceso al dashboard.
        
        Args:
            usuario_id: ID del usuario en la base de datos
            telefono: Número de teléfono del usuario
            
        Returns:
            Token JWT como string
        """
        try:
            # Crear payload del token
            payload = {
                'usuario_id': usuario_id,
                'telefono': telefono,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION_HOURS),
                'iat': datetime.datetime.utcnow(),
                'type': 'dashboard_access'
            }
            
            # Generar token
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            logger.info(f"Token generado para usuario {usuario_id}")
            return token

        except Exception as e:
            logger.error(f"Error generando token: {e}")
            log_security_event(logger, "token_generation_failed", f"usuario_id={usuario_id}", "ERROR")
            raise
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        Verifica y decodifica un token JWT.
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Dict con datos del usuario si es válido, None si no
        """
        try:
            # Decodificar y verificar token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Verificar que es un token de dashboard
            if payload.get('type') != 'dashboard_access':
                log_security_event(logger, "invalid_token_type", f"type={payload.get('type')}", "WARNING")
                return None

            logger.info(f"Token verificado para usuario {payload.get('usuario_id')}")
            return {
                'usuario_id': payload.get('usuario_id'),
                'telefono': payload.get('telefono'),
                'exp': payload.get('exp')
            }

        except jwt.ExpiredSignatureError:
            log_security_event(logger, "expired_token", "Token expirado", "WARNING")
            return None
        except jwt.InvalidTokenError as e:
            log_security_event(logger, "invalid_token", str(e), "WARNING")
            return None
        except Exception as e:
            logger.error(f"Error verificando token: {e}")
            log_security_event(logger, "token_verification_error", str(e), "ERROR")
            return None
    
    @staticmethod
    def generate_dashboard_link(usuario_id: int, telefono: str, base_url: str = None) -> str:
        """
        Genera un link completo al dashboard con token incluido.
        
        Args:
            usuario_id: ID del usuario
            telefono: Número de teléfono del usuario
            base_url: URL base del dashboard (default: settings)
            
        Returns:
            URL completa con token
        """
        token = AuthService.generate_dashboard_token(usuario_id, telefono)
        
        # URL base del dashboard - en producción vendrá de variable de entorno
        if base_url is None:
            base_url = getattr(settings, 'DASHBOARD_URL', 'https://loki-dashboard.vercel.app')
        
        dashboard_link = f"{base_url}/auth?token={token}"

        logger.info(f"Link de dashboard generado para usuario {usuario_id}")
        return dashboard_link


# Instancia global del servicio
auth_service = AuthService()
