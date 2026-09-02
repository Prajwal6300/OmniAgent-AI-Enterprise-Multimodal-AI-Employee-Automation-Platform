import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniAgent AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "default-insecure-secret-key-override-in-env"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/omniagent_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    JWT_SECRET: str = "jwt-secret-key-omniagent"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Storage
    STORAGE_PROVIDER: str = "minio"
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_BUCKET: str = "omniagent-documents"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"

    # AI Models
    DEFAULT_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 1536

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
