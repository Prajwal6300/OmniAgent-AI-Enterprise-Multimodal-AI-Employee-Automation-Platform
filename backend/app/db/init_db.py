from app.db.base import Base
from app.db.session import engine

async def init_db():
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead of create_all
        pass
