import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

import app.models  # noqa
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read ALEMBIC_DATABASE_URL or DATABASE_URL from environment variable
database_url = os.environ.get("ALEMBIC_DATABASE_URL") or os.environ.get("DATABASE_URL")

if not database_url:
    raise RuntimeError(
        "DATABASE_URL or ALEMBIC_DATABASE_URL environment variable must be set for Alembic migrations"
    )

# Alembic migrations require synchronous database URL: convert asyncpg to psycopg2 / default
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        connection.run_sync(do_run_migrations)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()