from functools import lru_cache
import os

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    PROJECT_NAME: str = Field("Loki Moodtracker API", env="PROJECT_NAME")
    VERSION: str = Field("0.1.0", env="PROJECT_VERSION")
    PROJECT_DESCRIPTION: str = Field(
        "API backend for Loki, the WhatsApp-based emotional companion.",
        env="PROJECT_DESCRIPTION",
    )
    API_V1_STR: str = Field("/api/v1", env="API_V1_STR")

    # Base de datos - Por defecto SQLite local, PostgreSQL en producción
    DATABASE_URL: str = Field(
        "sqlite:///./data/moodtracker.db",
        env="DATABASE_URL",
    )
    
    # Authentication & Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY", min_length=32)
    DASHBOARD_URL: str = Field(
        "http://localhost:3000",
        env="DASHBOARD_URL"
    )

    # CORS - Allowed origins for frontend
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    OPENAI_API_KEY: str | None = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Twilio WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str | None = Field(default=None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = Field(default=None, env="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str | None = Field(default="whatsapp:+14155238886", env="TWILIO_WHATSAPP_NUMBER")
    
    # Meta WhatsApp (legacy - mantener por compatibilidad)
    WHATSAPP_ACCESS_TOKEN: str | None = Field(default=None, env="WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_VERIFY_TOKEN: str | None = Field(default=None, env="WHATSAPP_VERIFY_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID: str | None = Field(default=None, env="WHATSAPP_PHONE_NUMBER_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
