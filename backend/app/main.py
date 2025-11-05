from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.routes.health import router as health_router
from app.api.routes.mood import router as mood_router
from app.api.routes.habits import router as habits_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.whatsapp import router as whatsapp_router
from app.api.routes.twilio import router as twilio_router  # Twilio WhatsApp
from app.api.routes.auth import router as auth_router  # Authentication
from app.api.routes.chat import router as chat_router
from app.api.routes.patterns import router as patterns_router
from app.api.routes.dashboard import router as dashboard_router  # Dashboard temporal
from app.core.config import settings
from app.core.logger import setup_logger
from app.core.sentry import init_sentry
from app.core.logging_config import setup_logging, set_audit_logger, get_logger
from app.core.logging_middleware import RequestLoggingMiddleware, SlowRequestMiddleware
from app.db.session import engine
from app.models import mood

# Inicializar sistema de logging estructurado
environment = 'production' if settings.ENV == 'production' else 'development'
_, audit_logger = setup_logging(
    environment=environment,
    log_level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else 'INFO',
    enable_console=True,
    enable_file=True,
    enable_audit=True,
)
if audit_logger:
    set_audit_logger(audit_logger)

# Logger para este módulo
logger = get_logger(__name__)

# Initialize Sentry for error tracking
init_sentry()


def create_app() -> FastAPI:
    """Application factory to enable future configuration hooks."""
    app = FastAPI(
        title="MoodTracker API - Loki",
        version="0.1.0",
        description="API for Loki, the WhatsApp-based emotional companion",
    )

    # Configurar rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ===== Middlewares de Logging =====
    # Agregar middlewares de logging (ANTES de CORS)
    app.add_middleware(SlowRequestMiddleware, threshold_ms=1000)  # Warn si >1s
    app.add_middleware(RequestLoggingMiddleware)  # Loggea todas las requests

    # Configurar CORS de forma restrictiva
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # NOTA: Las tablas se crean usando migraciones de Alembic
    # Para aplicar migraciones: cd backend && python -m alembic upgrade head
    # Para crear nuevas migraciones: python -m alembic revision --autogenerate -m "Descripción"
    # NO usar Base.metadata.create_all() en producción - puede sobrescribir datos

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])  # Dashboard temporal
    app.include_router(auth_router, prefix=settings.API_V1_STR + "/auth", tags=["authentication"])
    app.include_router(mood_router, prefix=settings.API_V1_STR, tags=["mood"])
    app.include_router(habits_router, prefix=settings.API_V1_STR, tags=["habits"])
    app.include_router(analytics_router, prefix=settings.API_V1_STR, tags=["analytics"])
    app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
    app.include_router(twilio_router, prefix="/twilio", tags=["twilio"])  # Twilio WhatsApp
    app.include_router(chat_router, prefix=settings.API_V1_STR + "/chat", tags=["chat"])
    app.include_router(patterns_router, prefix=settings.API_V1_STR + "/patterns", tags=["patterns"])

    return app


app = create_app()
