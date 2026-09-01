# Backend — Database Layer (SQLAlchemy 2.0 & PostgreSQL 16)

## Status
**Status:** ✅ IMPLEMENTED (Asyncpg, SQLAlchemy 2.0 & Alembic)

---

## 1. Database Architecture Overview

OmniAgent AI utilizes **PostgreSQL 16** with the **`pgvector`** extension as a unified database engine for transactional relational entities (users, workflows, approvals, audit logs) and high-dimensional vector embeddings.

```mermaid
flowchart TD
    A[FastAPI Request Coroutine] --> B[AsyncSession Dependency: get_db]
    B --> C[SQLAlchemy 2.0 Async Engine]
    C --> D[Asyncpg Connection Pool: min_size=10, max_size=50]
    
    D --> E[(PostgreSQL 16 Relational Tables)]
    D --> F[(pgvector Document & Embedding Tables)]
    
    G[Alembic Migration CLI] --> H[Execute Version-Controlled DDL Scripts]
    H --> E & F
```

---

## 2. Asynchronous Session Management

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```
