#!/usr/bin/env python
import os
os.chdir(r"F:\Projects\OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform\backend")

# Set DATABASE_URL - use postgresql:// which defaults to psycopg2 synchronous
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/omniagent_db'

from alembic.config import Config
from alembic import command

config = Config('alembic.ini')

# Import all models to register them in Base.metadata
from app.db.base import Base
import app.models  # noqa - registers all 27 models

# Generate migration using Alembic's autogenerate
# Set the sqlalchemy.url main option so env.py can find it
config.set_main_option("sqlalchemy.url", os.environ['DATABASE_URL'])

# Now call revision - the env.py will read the URL from config
command.revision(config, autogenerate=True, message='initial schema')

print("\nMigration generated successfully!")
print("Check migrations/versions/ for the new file.")