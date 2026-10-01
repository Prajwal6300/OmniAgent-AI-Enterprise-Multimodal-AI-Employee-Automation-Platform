from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _create_engine_safe():
    """Create async engine, with fallback for testing/development."""
    db_url = settings.DATABASE_URL
    if not db_url:
        db_url = "sqlite+aiosqlite:///:memory:"

    # Configure engine kwargs based on database dialect
    kwargs = {
        "echo": settings.DEBUG,
        "future": True,
    }

    # SQLite with aiosqlite doesn't support pool_size/max_overflow
    if not db_url.startswith("sqlite"):
        # Pool settings for asyncpg (PostgreSQL)
        kwargs["pool_size"] = 20
        kwargs["max_overflow"] = 10

    try:
        engine = create_async_engine(db_url, **kwargs)
        return engine
    except Exception as e:
        # If the URL is invalid, fall back to SQLite in-memory for testing
        if "Could not parse SQLAlchemy URL" in str(e):
            engine = create_async_engine(
                "sqlite+aiosqlite:///:memory:",
                echo=False,
                future=True,
            )
            return engine
        raise


engine = _create_engine_safe()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()