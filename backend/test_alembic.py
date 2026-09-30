import os
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/omniagent_db"

# Now run alembic
import sys
sys.path.insert(0, '.')

from alembic.config import Config

config = Config("alembic.ini")
# Override the URL
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

# Check it worked
url = config.get_main_option("sqlalchemy.url")
print(f"URL set correctly: {url}")
assert url == os.environ["DATABASE_URL"], f"URL mismatch: {url} != {os.environ['DATABASE_URL']}"
print("PASS: DATABASE_URL is correctly read from environment")