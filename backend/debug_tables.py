import os

os.chdir(r"F:\Projects\OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform\backend")

import app.models  # noqa
from app.db.base import Base

# Check Table attributes
table = Base.metadata.tables['users']
print("Table attributes:", [a for a in dir(table) if not a.startswith('_')])
print("\nColumns:", table.columns.keys())
print("\nForeign keys:", table.foreign_keys.keys())
print("\nUnique constraints:", table.constraints.keys())