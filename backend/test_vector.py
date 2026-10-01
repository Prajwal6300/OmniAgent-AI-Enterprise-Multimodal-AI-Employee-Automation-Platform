import os

os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5432/omniagent_db"

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["DATABASE_URL"])

with engine.connect() as conn:
    result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
    rows = result.fetchall()
    if rows:
        print("pgvector extension is already enabled")
    else:
        print("pgvector extension NOT enabled - need to add migration")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("pgvector extension created successfully")