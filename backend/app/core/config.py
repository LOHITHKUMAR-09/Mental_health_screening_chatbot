"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "MindEase - Mental Health Chatbot"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mindease_user:mindease_password@localhost:5432/mindease_db"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    LLM_TEMPERATURE: float = 0.5
    LLM_MAX_TOKENS: int = 512

    # ML
    ML_MODEL_PATH: str = "ml_models/best_model.pkl"
    ML_SCALER_PATH: str = "ml_models/scaler.pkl"

    # Crisis
    ICALL_HELPLINE: str = "9152987821"
    VANDREVALA_HELPLINE: str = "1860-2662-345"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
