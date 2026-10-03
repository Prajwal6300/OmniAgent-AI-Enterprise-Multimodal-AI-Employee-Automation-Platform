from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    OmniAgent AI — Production Configuration & Settings
    Strictly aligned to the fixed stack: OpenAI, Render, Supabase (pgvector & Storage), Redis.
    """

    # 1. Environment & Core
    PROJECT_NAME: str = "OmniAgent AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "production", "staging", "test"] = "development"
    DEBUG: bool = False

    # 2. Cryptographic Secrets (Required >= 32 chars in production)
    SECRET_KEY: str = Field(
        default="insecure-dev-secret-key-change-in-production-min32chars"
    )
    JWT_SECRET: str = Field(
        default="insecure-dev-jwt-secret-change-in-production-min32chars"
    )
    ENCRYPTION_KEY: str = Field(
        default="0123456789abcdef0123456789abcdef"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://omniagent.ai",
    ]

    # 3. Database (Supabase PostgreSQL with pgvector)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/omniagent_db"
    )
    ALEMBIC_DATABASE_URL: str | None = None

    # 4. Redis (Render Key Value / Upstash / Celery)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # 5. LLM & Embeddings (OpenAI API Only)
    OPENAI_API_KEY: str = Field(default="")
    DEFAULT_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSION: int = 1536

    # 6. Object Storage (S3/R2 compatible, local in dev)
    STORAGE_PROVIDER: Literal["s3", "local"] = "local"
    STORAGE_LOCAL_DIR: str = "storage/documents"
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    S3_ENDPOINT: str = ""
    S3_REGION: str = "auto"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "documents"

    # Deprecated Supabase aliases — accepted with a logged warning
    SUPABASE_S3_ENDPOINT: str = Field(default="", alias="SUPABASE_S3_ENDPOINT")
    SUPABASE_S3_REGION: str = Field(default="", alias="SUPABASE_S3_REGION")
    SUPABASE_S3_ACCESS_KEY: str = Field(default="", alias="SUPABASE_S3_ACCESS_KEY")
    SUPABASE_S3_SECRET_KEY: str = Field(default="", alias="SUPABASE_S3_SECRET_KEY")
    SUPABASE_BUCKET: str = Field(default="documents", alias="SUPABASE_BUCKET")

    # 7. Optional Integrations (SMTP & Sentry)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@omniagent.ai"
    SMTP_USE_TLS: bool = True
    SENTRY_DSN: str = ""

    # 8. Guardrails & Limits
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.05
    DATABASE_AGENT_MAX_ROWS: int = 100
    DATABASE_AGENT_MAX_LIMIT: int = 500
    DATABASE_AGENT_QUERY_TIMEOUT_SECONDS: int = 10
    VISION_MAX_FILE_SIZE_MB: int = 10
    VISION_MAX_WIDTH: int = 4096
    VISION_MAX_HEIGHT: int = 4096
    VISION_MAX_IMAGE_PIXELS: int = 16777216
    VISION_OCR_ENABLED: bool = True
    VISION_OBJECT_DETECTION_ENABLED: bool = True
    REASONING_MAX_AGENT_CALLS: int = 5
    REASONING_MAX_AGENT_DEPTH: int = 3
    REASONING_AGENT_TIMEOUT_SECONDS: int = 30
    ACTION_APPROVAL_EXPIRATION_MINUTES: int = 30
    ACTION_MAX_PAYLOAD_SIZE_KB: int = 256
    ACTION_EXECUTION_TIMEOUT_SECONDS: int = 30
    ORCHESTRATION_MAX_STEPS: int = 20
    ORCHESTRATION_MAX_AGENT_CALLS: int = 10
    ORCHESTRATION_MAX_EXECUTION_SECONDS: int = 120
    WORKFLOW_MAX_STEPS: int = 30
    WORKFLOW_MAX_EXECUTION_SECONDS: int = 300
    APPROVAL_EXPIRATION_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def map_deprecated_supabase_aliases(self) -> "Settings":
        """Map deprecated SUPABASE_S3_* env vars to new S3_* names with a warning."""
        import warnings

        supabase_to_s3 = {
            self.SUPABASE_S3_ENDPOINT: "S3_ENDPOINT",
            self.SUPABASE_S3_REGION: "S3_REGION",
            self.SUPABASE_S3_ACCESS_KEY: "S3_ACCESS_KEY",
            self.SUPABASE_S3_SECRET_KEY: "S3_SECRET_KEY",
        }

        any_mapped = False
        for supabase_val, new_attr in supabase_to_s3.items():
            if supabase_val and not getattr(self, new_attr, None):
                setattr(self, new_attr, supabase_val)
                any_mapped = True

        if any_mapped and self.STORAGE_PROVIDER != "supabase":
            warnings.warn(
                "Deprecated SUPABASE_S3_* environment variables detected. "
                "Migrate to S3_ENDPOINT, S3_REGION, S3_ACCESS_KEY, S3_SECRET_KEY.",
                UserWarning,
            )

        # Also handle the bucket: if SUPABASE_BUCKET was set and S3_BUCKET wasn't
        if self.SUPABASE_BUCKET and not self.S3_BUCKET:
            self.S3_BUCKET = self.SUPABASE_BUCKET

        return self

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        """Fail fast at startup if configuration is invalid for production."""
        if self.ENVIRONMENT == "production":
            insecure_defaults = {
                "default-insecure-secret-key-override-in-env",
                "jwt-secret-key-omniagent",
                "insecure-dev-secret-key-change-in-production-min32chars",
                "insecure-dev-jwt-secret-change-in-production-min32chars",
                "0123456789abcdef0123456789abcdef",
            }

            # 1. Cryptographic Secrets
            if not self.SECRET_KEY or self.SECRET_KEY in insecure_defaults or len(self.SECRET_KEY) < 32:
                raise ValueError("In production, SECRET_KEY must be a unique non-default secret with >= 32 characters.")
            if not self.JWT_SECRET or self.JWT_SECRET in insecure_defaults or len(self.JWT_SECRET) < 32:
                raise ValueError("In production, JWT_SECRET must be a unique non-default secret with >= 32 characters.")
            if self.SECRET_KEY == self.JWT_SECRET:
                raise ValueError("In production, SECRET_KEY and JWT_SECRET must not be identical.")
            if not self.ENCRYPTION_KEY or self.ENCRYPTION_KEY in insecure_defaults or len(self.ENCRYPTION_KEY) < 32:
                raise ValueError("In production, ENCRYPTION_KEY must be a unique non-default secret with >= 32 characters.")

            # 2. Database & Redis requirements
            if not self.DATABASE_URL or "localhost" in self.DATABASE_URL:
                raise ValueError("In production, DATABASE_URL must point to a remote managed PostgreSQL database (e.g. Supabase).")
            if not self.REDIS_URL:
                raise ValueError("In production, REDIS_URL must be configured.")

            # 3. OpenAI requirements
            if not self.OPENAI_API_KEY:
                raise ValueError("In production, OPENAI_API_KEY must be set.")

            # 4. Storage provider requirement
            if self.STORAGE_PROVIDER == "local":
                if self.ENVIRONMENT == "production":
                    raise ValueError("In production, STORAGE_PROVIDER cannot be 'local'.")
                else:
                    import warnings
                    warnings.warn(
                        "STORAGE_PROVIDER=local is only allowed in development. "
                        "Set STORAGE_PROVIDER=s3 for production deployments.",
                        UserWarning,
                    )
            if self.STORAGE_PROVIDER == "supabase":
                import warnings
                warnings.warn(
                    "STORAGE_PROVIDER=supabase is deprecated. Use STORAGE_PROVIDER=s3 instead.",
                    UserWarning,
                )
            if self.STORAGE_PROVIDER not in ("s3", "local"):
                raise ValueError("STORAGE_PROVIDER must be one of: s3, local.")

            # Check that S3 env vars are set when STORAGE_PROVIDER is s3
            if self.STORAGE_PROVIDER == "s3":
                if not self.S3_ENDPOINT:
                    raise ValueError("When STORAGE_PROVIDER is 's3', S3_ENDPOINT must be set.")
                if not self.S3_ACCESS_KEY:
                    raise ValueError("When STORAGE_PROVIDER is 's3', S3_ACCESS_KEY must be set.")
                if not self.S3_SECRET_KEY:
                    raise ValueError("When STORAGE_PROVIDER is 's3', S3_SECRET_KEY must be set.")
                if not self.S3_BUCKET:
                    raise ValueError("When STORAGE_PROVIDER is 's3', S3_BUCKET must be set.")

            # Log deprecation warnings for old Supabase aliases
            if self.SUPABASE_S3_ENDPOINT and self.STORAGE_PROVIDER != "supabase":
                import warnings
                warnings.warn(
                    "SUPABASE_S3_ENDPOINT is set but STORAGE_PROVIDER is not 'supabase'. "
                    "SUPABASE_S3_* names are deprecated; use S3_ENDPOINT, S3_REGION, etc. instead.",
                    UserWarning,
                )

            # 5. Embedding dimension check
            if self.EMBEDDING_DIMENSION != 1536:
                raise ValueError("EMBEDDING_DIMENSION must be 1536 to match the database pgvector column.")

        return self


settings = Settings()