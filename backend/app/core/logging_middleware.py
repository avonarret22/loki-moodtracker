"""
Middleware para logging de requests HTTP.

Loggea todas las requests con:
- Request ID único
- Tiempo de respuesta
- Status code
- User ID (si está autenticado)
- Errores y excepciones
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import get_logger, set_request_context, clear_request_context

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que loggea todas las HTTP requests.
    
    Features:
    - Genera request_id único para tracing
    - Loggea inicio y fin de request
    - Mide tiempo de respuesta
    - Captura errores y excepciones
    - Inyecta contexto en logs subsiguientes
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa request y loggea información relevante.
        """
        # Generar request ID único
        request_id = str(uuid.uuid4())
        
        # Obtener user_id si está en el request state (seteado por auth)
        user_id = getattr(request.state, 'user_id', None)
        
        # Establecer contexto para todos los logs subsiguientes
        set_request_context(request_id=request_id, user_id=user_id)
        
        # Log inicio de request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={'extra_data': {
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params),
                'client_host': request.client.host if request.client else None,
            }}
        )
        
        # Medir tiempo de respuesta
        start_time = time.time()
        
        try:
            # Procesar request
            response = await call_next(request)
            
            # Calcular duración
            duration_ms = (time.time() - start_time) * 1000
            
            # Log fin de request exitoso
            logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms",
                extra={'extra_data': {
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration_ms, 2),
                }}
            )
            
            # Agregar request_id a headers de respuesta para debugging
            response.headers['X-Request-ID'] = request_id
            
            return response
        
        except Exception as e:
            # Calcular duración hasta el error
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.exception(
                f"Request failed: {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration_ms:.2f}ms",
                extra={'extra_data': {
                    'method': request.method,
                    'path': request.url.path,
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'duration_ms': round(duration_ms, 2),
                }}
            )
            
            # Re-lanzar excepción para que FastAPI la maneje
            raise
        
        finally:
            # Limpiar contexto
            clear_request_context()


class SlowRequestMiddleware(BaseHTTPMiddleware):
    """
    Middleware que loggea warnings para requests lentos.
    
    Ayuda a identificar endpoints que necesitan optimización.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        threshold_ms: float = 1000.0,  # 1 segundo
    ):
        super().__init__(app)
        self.threshold_ms = threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa request y loggea si es muy lento.
        """
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        if duration_ms > self.threshold_ms:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} - "
                f"Duration: {duration_ms:.2f}ms (threshold: {self.threshold_ms}ms)",
                extra={'extra_data': {
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': round(duration_ms, 2),
                    'threshold_ms': self.threshold_ms,
                }}
            )
        
        return response
