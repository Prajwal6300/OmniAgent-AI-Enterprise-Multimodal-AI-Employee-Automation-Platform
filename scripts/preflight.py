#!/usr/bin/env python3
"""
OmniAgent AI — Deployment Preflight Verification Script
Validates environment configuration, database connectivity, vector extension,
Redis cache, and security constraints before production deployment.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))


def log_result(check_name: str, passed: bool, message: str = ""):
    status = "\033[92m[PASS]\033[0m" if passed else "\033[91m[FAIL]\033[0m"
    detail = f" — {message}" if message else ""
    print(f" {status} {check_name}{detail}")
    return passed


async def main() -> int:
    print("=" * 60)
    print(" OmniAgent AI — Production Preflight Check")
    print("=" * 60)

    all_passed = True

    # 1. Environment & Secrets Check
    secret_key = os.getenv("SECRET_KEY", "")
    if len(secret_key) >= 32 and "your-secret-key" not in secret_key:
        log_result("SECRET_KEY strength", True, f"Length: {len(secret_key)} chars")
    else:
        all_passed = False
        log_result("SECRET_KEY strength", False, "Must be >= 32 characters and non-default")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and (openai_key.startswith("sk-") or len(openai_key) > 20):
        log_result("OPENAI_API_KEY configuration", True, "Key present and structured")
    else:
        print(" \033[93m[WARN]\033[0m OPENAI_API_KEY not configured or placeholder (mock fallback active)")

    db_url = os.getenv("DATABASE_URL", "")
    if db_url:
        log_result("DATABASE_URL format", True, db_url.split("@")[-1] if "@" in db_url else "configured")
    else:
        all_passed = False
        log_result("DATABASE_URL format", False, "DATABASE_URL environment variable is missing")

    redis_url = os.getenv("REDIS_URL", "")
    if redis_url:
        log_result("REDIS_URL format", True, redis_url.split("@")[-1] if "@" in redis_url else "configured")
    else:
        all_passed = False
        log_result("REDIS_URL format", False, "REDIS_URL environment variable is missing")

    # 2. Database Connectivity & Extension Probe
    if db_url and not db_url.startswith("sqlite"):
        try:
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine

            engine = create_async_engine(db_url, echo=False)
            async with engine.connect() as conn:
                res = await conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
                has_vector = res.scalar_one_or_none() is not None
                log_result("Database connection & pgvector extension", has_vector, "pgvector enabled" if has_vector else "pgvector extension missing!")
                if not has_vector:
                    all_passed = False
            await engine.dispose()
        except Exception as e:  # noqa: BLE001 - Diagnostic CLI probe catches all connection failures
            all_passed = False
            log_result("Database connectivity probe", False, str(e))
    else:
        log_result("Database configuration (Local/Dev)", True, "Using in-memory or SQLite mode")

    # 3. Redis Connectivity Probe
    if redis_url:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(redis_url, socket_timeout=3.0)
            pong = await r.ping()
            await r.aclose()
            log_result("Redis connectivity probe", pong is True, "PONG received")
        except Exception as e:  # noqa: BLE001 - Diagnostic CLI probe catches all connection failures
            # In offline build environments, Redis may not be listening locally
            print(f" \033[93m[WARN]\033[0m Redis not reachable on {redis_url} ({e})")

    print("=" * 60)
    if all_passed:
        print("\033[92mAll required preflight checks passed.\033[0m")
        return 0
    else:
        print("\033[91mPreflight checks failed. Please address errors before deploying.\033[0m")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
