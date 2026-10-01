import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/omniagent_db"

from alembic import command
from alembic.config import Config

config = Config("alembic.ini")
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Upgrade to head
command.upgrade(config, "head")
print("Upgrade to head completed successfully")