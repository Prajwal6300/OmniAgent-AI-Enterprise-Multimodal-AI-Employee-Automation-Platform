import os
os.chdir(r"F:\Projects\OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform\backend")

# Set up environment
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/omniagent_db'

from alembic.config import Config
from alembic import script

config = Config('alembic.ini')
config.set_offline_mode()

# Generate the migration
from alembic import command
command.revision(config, autogenerate=True, message='initial schema')

print("\nMigration generated successfully!")
print("Check migrations/versions/ for the new file.")