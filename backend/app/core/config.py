import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _validate_secret_key(value: str, min_len: int = 32) -> str:
    """Validate that a secret key is not the default and meets minimum length."""
    default_keys = {
        "default-insecure-secret-key-override-in-env",
        "jwt-secret-key-omniagent",
    }
    if value in default_keys:
        raise ValueError(
            f"Secret key must be set via environment variable, not using default '{value}'"
        )
    if len(value) < min_len:
        raise ValueError(f"Secret key must be at least {min_len} characters, got {len(value)}")
    return value


class Settings(BaseSettings):
    PROJECT_NAME: str = "OmniAgent AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = _validate_secret_key(
        os.getenv("SECRET_KEY", "default-insecure-secret-key-override-in-env"), min_len=32
    )
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    JWT_SECRET: str = _validate_secret_key(
        os.getenv("JWT_SECRET", "jwt-secret-key-omniagent"), min_len=32
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database - MUST be set via DATABASE_URL environment variable
    # Local Docker: postgresql+asyncpg://USER:PASSWORD@host:port/database
    # Production Supabase: postgres://USER:PASSWORD@host:port/database?sslmode=require
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Storage
    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_DIR: str = "storage/documents"
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_BUCKET: str = "omniagent-documents"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"

    # AI Models
    DEFAULT_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "deterministic"  # "deterministic" | "mock" | "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 1536

    # RAG Configuration
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.05

    # Reranker Configuration
    RERANKER_PROVIDER: str = "cohere"  # "cohere" | "cross_encoder"
    COHERE_API_KEY: str = ""
    COHERE_RERANK_MODEL: str = "rerank-english-v3.0"

    # Database Agent Configuration
    DATABASE_AGENT_MAX_ROWS: int = 100
    DATABASE_AGENT_MAX_LIMIT: int = 500
    DATABASE_AGENT_QUERY_TIMEOUT_SECONDS: int = 10

    # Vision Agent Configuration
    VISION_MAX_FILE_SIZE_MB: int = 10
    VISION_MAX_WIDTH: int = 4096
    VISION_MAX_HEIGHT: int = 4096
    VISION_MAX_IMAGE_PIXELS: int = 16777216
    VISION_OCR_ENABLED: bool = True
    VISION_OBJECT_DETECTION_ENABLED: bool = True
    VISION_PROVIDER: str = "openai"
    VISION_MODEL: str = "gpt-4o"
    VISION_STORAGE_DIR: str = "storage/images"

    # Reasoning Agent Configuration
    REASONING_MAX_AGENT_CALLS: int = 5
    REASONING_MAX_AGENT_DEPTH: int = 3
    REASONING_AGENT_TIMEOUT_SECONDS: int = 30
    REASONING_PROVIDER: str = "hybrid"
    REASONING_MODEL: str = "gpt-4o"

    # Action Agent Configuration
    ACTION_APPROVAL_EXPIRATION_MINUTES: int = 30
    ACTION_MAX_PAYLOAD_SIZE_KB: int = 256
    ACTION_EXECUTION_TIMEOUT_SECONDS: int = 30

    # Email Integration Configuration
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@omniagent.ai"

    # Orchestration Configuration
    ORCHESTRATION_MAX_STEPS: int = 20
    ORCHESTRATION_MAX_AGENT_CALLS: int = 10
    ORCHESTRATION_MAX_EXECUTION_SECONDS: int = 120
    ORCHESTRATION_MAX_RETRIES: int = 2

    # Workflow Automation Configuration
    WORKFLOW_MAX_STEPS: int = 30
    WORKFLOW_MAX_EXECUTION_SECONDS: int = 300

    # Approval Configuration
    APPROVAL_EXPIRATION_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def check_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT == "production" and self.SECRET_KEY == self.JWT_SECRET:
            raise ValueError(
                "SECRET_KEY and JWT_SECRET must not be equal in production environment"
            )
        return self


settings = Settings()