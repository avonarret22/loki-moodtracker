from functools import lru_cache
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    PROJECT_NAME: str = Field(default="Loki Moodtracker API", validation_alias="PROJECT_NAME")
    VERSION: str = Field(default="0.1.0", validation_alias="PROJECT_VERSION")
    PROJECT_DESCRIPTION: str = Field(
        default="API backend for Loki, the WhatsApp-based emotional companion.",
        validation_alias="PROJECT_DESCRIPTION",
    )
    API_V1_STR: str = Field(default="/api/v1", validation_alias="API_V1_STR")

    # Base de datos - Por defecto SQLite local, PostgreSQL en producción
    DATABASE_URL: str = Field(
        default="sqlite:///./data/moodtracker.db",
        validation_alias="DATABASE_URL",
    )
    
    # Authentication & Security
    SECRET_KEY: str = Field(..., min_length=32, validation_alias="SECRET_KEY")
    DASHBOARD_URL: str = Field(
        default="http://localhost:3000",
        validation_alias="DASHBOARD_URL"
    )

    # CORS - Allowed origins for frontend
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000"],
        validation_alias="CORS_ORIGINS"
    )
    
    OPENAI_API_KEY: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    
    # Twilio WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str | None = Field(default=None, validation_alias="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = Field(default=None, validation_alias="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str | None = Field(default="whatsapp:+14155238886", validation_alias="TWILIO_WHATSAPP_NUMBER")
    
    # Meta WhatsApp (legacy - mantener por compatibilidad)
    WHATSAPP_ACCESS_TOKEN: str | None = Field(default=None, validation_alias="WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_VERIFY_TOKEN: str | None = Field(default=None, validation_alias="WHATSAPP_VERIFY_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID: str | None = Field(default=None, validation_alias="WHATSAPP_PHONE_NUMBER_ID")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    ENV: str = Field(default="development", validation_alias="ENV")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
