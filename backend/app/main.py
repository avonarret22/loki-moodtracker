from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.mood import router as mood_router
from app.api.routes.habits import router as habits_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.whatsapp import router as whatsapp_router
from app.api.routes.chat import router as chat_router
from app.api.routes.patterns import router as patterns_router  # Nuevo
from app.core.config import settings
from app.db.session import engine
from app.models import mood


def create_app() -> FastAPI:
    """Application factory to enable future configuration hooks."""
    app = FastAPI(
        title="MoodTracker API - Loki",
        version="0.1.0",
        description="API for Loki, the WhatsApp-based emotional companion",
    )

    # Configurar CORS para permitir el frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, especificar los dominios permitidos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Crear las tablas en la base de datos
    mood.Base.metadata.create_all(bind=engine)

    # Include routers
    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(mood_router, prefix=settings.API_V1_STR, tags=["mood"])
    app.include_router(habits_router, prefix=settings.API_V1_STR, tags=["habits"])
    app.include_router(analytics_router, prefix=settings.API_V1_STR, tags=["analytics"])
    app.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
    app.include_router(chat_router, prefix=settings.API_V1_STR + "/chat", tags=["chat"])
    app.include_router(patterns_router, prefix=settings.API_V1_STR + "/patterns", tags=["patterns"])  # Nuevo

    return app


app = create_app()
