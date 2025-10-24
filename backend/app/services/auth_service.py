"""
Servicio de autenticación con JWT para dashboard.
Genera tokens seguros para acceso al dashboard sin password.
"""
import jwt
import datetime
from typing import Optional, Dict
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Secret key para JWT - en producción debe venir de variable de entorno
JWT_SECRET = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "loki-secret-key-change-in-production"
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
            
            logger.info(f"✅ Token generado para usuario {usuario_id}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Error generando token: {e}")
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
                logger.warning("⚠️ Token no es de tipo dashboard_access")
                return None
            
            logger.info(f"✅ Token verificado para usuario {payload.get('usuario_id')}")
            return {
                'usuario_id': payload.get('usuario_id'),
                'telefono': payload.get('telefono'),
                'exp': payload.get('exp')
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("⚠️ Token expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ Token inválido: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error verificando token: {e}")
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
        
        logger.info(f"🔗 Link de dashboard generado para usuario {usuario_id}")
        return dashboard_link


# Instancia global del servicio
auth_service = AuthService()
