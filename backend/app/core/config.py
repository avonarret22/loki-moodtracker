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

    # Para desarrollo local usamos SQLite, en producción se puede usar PostgreSQL
    DATABASE_URL: str = Field(
        "sqlite:///./moodtracker.db",
        env="DATABASE_URL",
    )
    OPENAI_API_KEY: str | None = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
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
