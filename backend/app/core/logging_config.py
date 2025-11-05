"""
Sistema de logging estructurado para Loki Moodtracker.

Características:
- Logging estructurado con JSON format para producción
- Rotación de archivos automática
- Niveles de log configurables por módulo
- Integración con Sentry para errores críticos
- Audit logging para operaciones sensibles
- Context injection (request_id, user_id, etc.)
"""
import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Variables de contexto para request tracing
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[int]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Formatter que genera logs en formato JSON estructurado.
    
    Incluye campos estándar + contexto de request si está disponible.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea un log record como JSON.
        
        Args:
            record: LogRecord de Python logging
            
        Returns:
            String JSON con todos los campos del log
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Agregar contexto de request si existe
        request_id = request_id_var.get()
        if request_id:
            log_data['request_id'] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data['user_id'] = user_id
        
        # Agregar exception info si existe
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Agregar campos extra si existen
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class SimpleFormatter(logging.Formatter):
    """
    Formatter simple para desarrollo con colores (si terminal lo soporta).
    """
    
    # Colores ANSI para diferentes niveles
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea un log record de forma legible para desarrollo.
        """
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET if color else ''
        
        # Formato: [TIMESTAMP] LEVEL - logger - message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        base_msg = f"[{timestamp}] {color}{record.levelname:8}{reset} - {record.name:25} - {record.getMessage()}"
        
        # Agregar contexto si existe
        context_parts = []
        request_id = request_id_var.get()
        if request_id:
            context_parts.append(f"request_id={request_id}")
        
        user_id = user_id_var.get()
        if user_id:
            context_parts.append(f"user_id={user_id}")
        
        if context_parts:
            base_msg += f" [{', '.join(context_parts)}]"
        
        # Agregar exception si existe
        if record.exc_info:
            base_msg += '\n' + self.formatException(record.exc_info)
        
        return base_msg


class AuditLogger:
    """
    Logger especializado para audit trail de operaciones sensibles.
    
    Registra todas las operaciones que modifican datos críticos:
    - Creación/actualización/eliminación de usuarios
    - Cambios en hábitos
    - Accesos a endpoints protegidos
    - Errores de autenticación
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_user_created(self, user_id: int, telefono: str, **kwargs):
        """Registra creación de usuario."""
        self.logger.info(
            f"User created: user_id={user_id}, telefono={telefono}",
            extra={'extra_data': {
                'action': 'user_created',
                'user_id': user_id,
                'telefono': telefono,
                **kwargs
            }}
        )
    
    def log_user_accessed(self, user_id: int, endpoint: str, **kwargs):
        """Registra acceso a datos de usuario."""
        self.logger.info(
            f"User data accessed: user_id={user_id}, endpoint={endpoint}",
            extra={'extra_data': {
                'action': 'user_accessed',
                'user_id': user_id,
                'endpoint': endpoint,
                **kwargs
            }}
        )
    
    def log_habito_created(self, user_id: int, habito_id: int, nombre: str, **kwargs):
        """Registra creación de hábito."""
        self.logger.info(
            f"Habit created: user_id={user_id}, habito_id={habito_id}, nombre={nombre}",
            extra={'extra_data': {
                'action': 'habito_created',
                'user_id': user_id,
                'habito_id': habito_id,
                'nombre': nombre,
                **kwargs
            }}
        )
    
    def log_habito_updated(self, user_id: int, habito_id: int, changes: Dict[str, Any], **kwargs):
        """Registra actualización de hábito."""
        self.logger.info(
            f"Habit updated: user_id={user_id}, habito_id={habito_id}",
            extra={'extra_data': {
                'action': 'habito_updated',
                'user_id': user_id,
                'habito_id': habito_id,
                'changes': changes,
                **kwargs
            }}
        )
    
    def log_habito_deleted(self, user_id: int, habito_id: int, **kwargs):
        """Registra eliminación de hábito."""
        self.logger.warning(
            f"Habit deleted: user_id={user_id}, habito_id={habito_id}",
            extra={'extra_data': {
                'action': 'habito_deleted',
                'user_id': user_id,
                'habito_id': habito_id,
                **kwargs
            }}
        )
    
    def log_auth_failure(self, telefono: Optional[str], reason: str, **kwargs):
        """Registra fallo de autenticación."""
        self.logger.warning(
            f"Auth failure: telefono={telefono}, reason={reason}",
            extra={'extra_data': {
                'action': 'auth_failure',
                'telefono': telefono,
                'reason': reason,
                **kwargs
            }}
        )
    
    def log_rate_limit_exceeded(self, endpoint: str, identifier: str, **kwargs):
        """Registra exceso de rate limit."""
        self.logger.warning(
            f"Rate limit exceeded: endpoint={endpoint}, identifier={identifier}",
            extra={'extra_data': {
                'action': 'rate_limit_exceeded',
                'endpoint': endpoint,
                'identifier': identifier,
                **kwargs
            }}
        )


# ===== Configuración de Niveles por Módulo =====

LOG_LEVELS = {
    # Módulos de aplicación
    'app.api': logging.INFO,
    'app.services': logging.INFO,
    'app.crud': logging.INFO,
    'app.core': logging.INFO,
    
    # SQLAlchemy - solo warnings en producción
    'sqlalchemy.engine': logging.WARNING,
    'sqlalchemy.pool': logging.WARNING,
    'sqlalchemy.orm': logging.WARNING,
    
    # FastAPI - info para monitoreo
    'fastapi': logging.INFO,
    'uvicorn': logging.INFO,
    'uvicorn.access': logging.WARNING,  # Menos verbose
    
    # Librerías externas - solo errores
    'httpx': logging.ERROR,
    'httpcore': logging.ERROR,
    'openai': logging.WARNING,
}


def setup_logging(
    environment: str = 'development',
    log_level: str = 'INFO',
    log_dir: Optional[Path] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_audit: bool = True,
) -> tuple[logging.Logger, Optional[AuditLogger]]:
    """
    Configura el sistema de logging completo.
    
    Args:
        environment: 'development' o 'production'
        log_level: Nivel base de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directorio para archivos de log (default: ./logs)
        enable_console: Si True, loggea a consola
        enable_file: Si True, loggea a archivo con rotación
        enable_audit: Si True, crea logger de auditoría
        
    Returns:
        Tuple con (root_logger, audit_logger)
    """
    # Configurar directorio de logs
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # Obtener root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Limpiar handlers existentes
    root_logger.handlers.clear()
    
    # ===== Console Handler =====
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if environment == 'production':
            # JSON format para producción
            console_handler.setFormatter(StructuredFormatter())
        else:
            # Format simple para desarrollo
            console_handler.setFormatter(SimpleFormatter())
        
        root_logger.addHandler(console_handler)
    
    # ===== File Handler con Rotación =====
    if enable_file:
        # Log principal - rotación diaria, mantener 30 días
        app_log_file = log_dir / 'loki_moodtracker.log'
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=app_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.DEBUG)
        
        if environment == 'production':
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(SimpleFormatter())
        
        root_logger.addHandler(file_handler)
        
        # Error log separado - solo errores y críticos
        error_log_file = log_dir / 'errors.log'
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8',
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(error_handler)
    
    # ===== Configurar niveles por módulo =====
    for logger_name, level in LOG_LEVELS.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # ===== Audit Logger =====
    audit_logger = None
    if enable_audit:
        audit_file = log_dir / 'audit.log'
        audit_handler = logging.handlers.TimedRotatingFileHandler(
            filename=audit_file,
            when='midnight',
            interval=1,
            backupCount=90,  # Mantener 90 días para auditoría
            encoding='utf-8',
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(StructuredFormatter())
        
        # Logger separado para audit trail
        logger = logging.getLogger('audit')
        logger.setLevel(logging.INFO)
        logger.addHandler(audit_handler)
        logger.propagate = False  # No propagar a root logger
        
        audit_logger = AuditLogger(logger)
    
    root_logger.info(f"Logging system initialized - environment={environment}, level={log_level}")
    
    return root_logger, audit_logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger (típicamente __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def set_request_context(request_id: Optional[str] = None, user_id: Optional[int] = None):
    """
    Establece el contexto de request para logging.
    
    Debe llamarse al inicio de cada request para que los logs incluyan esta info.
    
    Args:
        request_id: ID único del request
        user_id: ID del usuario autenticado (si aplica)
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)


def clear_request_context():
    """
    Limpia el contexto de request.
    
    Debe llamarse al final de cada request.
    """
    request_id_var.set(None)
    user_id_var.set(None)


# ===== Instancia Global =====
# Se inicializa en app startup
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> Optional[AuditLogger]:
    """Retorna el audit logger global."""
    return _audit_logger


def set_audit_logger(audit_logger: AuditLogger):
    """Establece el audit logger global."""
    global _audit_logger
    _audit_logger = audit_logger


if __name__ == "__main__":
    """
    Modo standalone para testing de logging.
    """
    print("🔧 Testing Logging System\n")
    
    # Setup logging
    logger, audit_logger = setup_logging(
        environment='development',
        log_level='DEBUG',
    )
    
    # Obtener loggers
    app_logger = get_logger('app.test')
    
    # Test diferentes niveles
    print("Testing log levels:")
    app_logger.debug("This is a DEBUG message")
    app_logger.info("This is an INFO message")
    app_logger.warning("This is a WARNING message")
    app_logger.error("This is an ERROR message")
    app_logger.critical("This is a CRITICAL message")
    
    # Test con contexto
    print("\nTesting with request context:")
    set_request_context(request_id="req-123", user_id=42)
    app_logger.info("Message with context")
    clear_request_context()
    
    # Test audit logger
    if audit_logger:
        print("\nTesting audit logger:")
        audit_logger.log_user_created(user_id=1, telefono="+1234567890", ip="127.0.0.1")
        audit_logger.log_habito_created(user_id=1, habito_id=10, nombre="Meditar")
        audit_logger.log_auth_failure(telefono="+9999999999", reason="Invalid token")
    
    # Test exception logging
    print("\nTesting exception logging:")
    try:
        1 / 0
    except Exception:
        app_logger.exception("An error occurred during division")
    
    print("\n✅ Logging test completed. Check ./logs/ directory for output files.")
