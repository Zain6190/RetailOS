import os
from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartStore AI"
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET: str = "supersecretkeychangeinproduction1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # Database
    DATABASE_URL: str = "sqlite:///./smartstore.db"

    # AI Configuration
    AI_PROVIDER: str = "groq"  # 'groq' or 'openai'
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Origins
    ALLOWED_ORIGINS: str = "http://localhost:4200,http://localhost:8000"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
