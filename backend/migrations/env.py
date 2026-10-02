import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

import app.models  # noqa
from app.db.base import Base

# Read ALEMBIC_DATABASE_URL or DATABASE_URL from environment variable
# config is set by Alembic when invoked via `alembic` command
database_url = os.environ.get("ALEMBIC_DATABASE_URL") or os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL or ALEMBIC_DATABASE_URL environment variable must be set for Alembic migrations"
    )

# Use the DATABASE_URL as-is (postgresql+asyncpg://) 
# Alembic will use async engine with run_sync pattern
target_metadata = Base.metadata


async def _run_migrations_async() -> None:
    """Run migrations inside an async engine context."""
    connectable = create_async_engine(database_url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(lambda sync_conn: context.run_migrations(sync_conn))

    await connectable.dispose()


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.
    This is useful for generating new migrations without connecting to the database.
    """
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in online mode.
    Uses async engine with run_sync to avoid needing a sync driver (psycopg).
    The DATABASE_URL stays as postgresql+asyncpg:// and Alembic runs
    within an async context using asyncio.
    """
    import asyncio

    asyncio.run(_run_migrations_async())


def main() -> None:
    """
    Entry point for alembic command.
    Checks offline/online mode and runs appropriate migrations.
    This is the pattern used by the `alembic` CLI command.
    """
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


if __name__ == "__main__":
    main()