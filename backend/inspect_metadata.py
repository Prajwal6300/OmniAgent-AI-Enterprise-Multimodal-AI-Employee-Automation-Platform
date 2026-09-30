import os
os.chdir(r"F:\Projects\OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform\backend")

# Set up environment
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/omniagent_db'

# Import all models first to register them in Base.metadata
from app.db.base import Base
import app.models  # noqa - registers all models

# Get all table names from metadata
tables = list(Base.metadata.tables.keys())
tables.sort()
print("Tables in Base.metadata:")
for t in tables:
    print(f"  - {t}")
print(f"\nTotal: {len(tables)}")