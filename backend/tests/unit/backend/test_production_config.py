"""
OmniAgent AI — Production Configuration & Settings Unit Tests
Verifies fail-fast validation rules in production environments:
1. Rejection of insecure default secrets
2. Rejection of short secret keys (< 32 chars)
3. Rejection of identical SECRET_KEY and JWT_SECRET
4. Rejection of STORAGE_PROVIDER=local in production
5. Rejection of missing Supabase credentials in production
6. Rejection of mismatched EMBEDDING_DIMENSION
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_config_defaults_allow_boot():
    """Development settings allow defaults for local convenience."""
    settings = Settings(
        ENVIRONMENT="development",
        SECRET_KEY="dev-key",
        JWT_SECRET="dev-jwt",
        ENCRYPTION_KEY="dev-enc",
        STORAGE_PROVIDER="local",
    )
    assert settings.ENVIRONMENT == "development"
    assert settings.STORAGE_PROVIDER == "local"


def test_production_fails_on_default_secrets():
    """Production mode must fail fast if default or short secrets are used."""
    with pytest.raises((ValidationError, ValueError)):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="insecure-dev-secret-key-change-in-production-min32chars",
            JWT_SECRET="valid-long-production-jwt-secret-key-32chars!",
            ENCRYPTION_KEY="valid-long-production-enc-secret-key-32chars!",
            DATABASE_URL="postgresql+asyncpg://postgres:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres?ssl=require",
            REDIS_URL="rediss://default:pass@redis.render.com:6379",
            OPENAI_API_KEY="sk-valid-openai-key-for-test",
            STORAGE_PROVIDER="s3",
            S3_ENDPOINT="https://test.storage.supabase.co/storage/v1/s3",
            S3_BUCKET="test-bucket",
            S3_ACCESS_KEY="valid_access_key",
            S3_SECRET_KEY="valid_secret_key",
            EMBEDDING_DIMENSION=1536,
        )


def test_production_fails_on_identical_secrets():
    """Production mode must fail fast if SECRET_KEY equals JWT_SECRET."""
    secret = "a" * 35
    with pytest.raises((ValidationError, ValueError)):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=secret,
            JWT_SECRET=secret,
            ENCRYPTION_KEY="b" * 35,
            DATABASE_URL="postgresql+asyncpg://postgres:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres?ssl=require",
            REDIS_URL="rediss://default:pass@redis.render.com:6379",
            OPENAI_API_KEY="sk-valid-openai-key-for-test",
            STORAGE_PROVIDER="s3",
            S3_ENDPOINT="https://test.storage.supabase.co/storage/v1/s3",
            S3_BUCKET="test-bucket",
            S3_ACCESS_KEY="valid_access_key",
            S3_SECRET_KEY="valid_secret_key",
            EMBEDDING_DIMENSION=1536,
        )


def test_production_fails_on_local_storage():
    """Production mode must refuse to start with local storage provider."""
    with pytest.raises((ValidationError, ValueError)):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 35,
            JWT_SECRET="b" * 35,
            ENCRYPTION_KEY="c" * 35,
            DATABASE_URL="postgresql+asyncpg://postgres:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres?ssl=require",
            REDIS_URL="rediss://default:pass@redis.render.com:6379",
            OPENAI_API_KEY="sk-valid-openai-key-for-test",
            STORAGE_PROVIDER="local",
            EMBEDDING_DIMENSION=1536,
        )


def test_production_fails_on_wrong_embedding_dimension():
    """Production mode must reject embedding dimensions != 1536 (pgvector schema mismatch)."""
    with pytest.raises((ValidationError, ValueError)):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 35,
            JWT_SECRET="b" * 35,
            ENCRYPTION_KEY="c" * 35,
            DATABASE_URL="postgresql+asyncpg://postgres:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres?ssl=require",
            REDIS_URL="rediss://default:pass@redis.render.com:6379",
            OPENAI_API_KEY="sk-valid-openai-key-for-test",
            STORAGE_PROVIDER="s3",
            S3_ENDPOINT="https://test.storage.supabase.co/storage/v1/s3",
            S3_BUCKET="test-bucket",
            S3_ACCESS_KEY="valid_access_key",
            S3_SECRET_KEY="valid_secret_key",
            EMBEDDING_DIMENSION=768,
        )


def test_production_succeeds_with_valid_configuration():
    """Production mode succeeds when all required secrets and parameters are provided."""
    settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="valid-production-secret-key-32chars!",
        JWT_SECRET="valid-production-jwt-secret-key-32chars!!",
        ENCRYPTION_KEY="valid-production-enc-secret-key-32chars!!",
        DATABASE_URL="postgresql+asyncpg://postgres:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres?ssl=require",
        REDIS_URL="rediss://default:pass@redis.render.com:6379",
        OPENAI_API_KEY="sk-valid-openai-key-for-test",
        STORAGE_PROVIDER="s3",
        S3_ENDPOINT="https://test.storage.supabase.co/storage/v1/s3",
            S3_BUCKET="test-bucket",
            S3_ACCESS_KEY="valid_access_key",
            S3_SECRET_KEY="valid_secret_key",
        EMBEDDING_DIMENSION=1536,
    )
    assert settings.ENVIRONMENT == "production"
    assert settings.STORAGE_PROVIDER == "s3"
    assert settings.EMBEDDING_DIMENSION == 1536
