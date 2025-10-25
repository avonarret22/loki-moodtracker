"""
Sistema de logging centralizado para Loki Mood Tracker.
Reemplaza todos los print() con logging estructurado.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Configura un logger con handlers para consola y archivo.

    Args:
        name: Nombre del logger (generalmente __name__)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Si True, también guarda logs en archivo

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Formato detallado
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo (si está habilitado)
    if log_to_file:
        # Crear directorio de logs si no existe
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Nombre de archivo con fecha
        log_filename = f"loki_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = logs_dir / log_filename

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Archivo guarda todo
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: Optional[int] = None,
    user_id: Optional[int] = None
) -> None:
    """
    Log estructurado para requests de API.

    Args:
        logger: Logger instance
        method: HTTP method (GET, POST, etc.)
        endpoint: Endpoint path
        status_code: HTTP status code
        user_id: ID del usuario (si está disponible)
    """
    extra_info = []
    if user_id:
        extra_info.append(f"user_id={user_id}")
    if status_code:
        extra_info.append(f"status={status_code}")

    extra_str = f" | {' | '.join(extra_info)}" if extra_info else ""

    logger.info(f"{method} {endpoint}{extra_str}")


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    details: str,
    severity: str = "WARNING"
) -> None:
    """
    Log para eventos de seguridad.

    Args:
        logger: Logger instance
        event_type: Tipo de evento (e.g., "invalid_token", "rate_limit")
        details: Detalles del evento
        severity: INFO, WARNING, ERROR, CRITICAL
    """
    log_method = getattr(logger, severity.lower(), logger.warning)
    log_method(f"SECURITY | {event_type} | {details}")


# Logger global para la aplicación
app_logger = setup_logger("loki", level=logging.DEBUG)
