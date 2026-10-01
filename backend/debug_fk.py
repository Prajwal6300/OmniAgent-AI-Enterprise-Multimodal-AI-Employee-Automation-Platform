import os

os.chdir(r"F:\Projects\OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform\backend")

import app.models  # noqa
from app.db.base import Base

table = Base.metadata.tables['users']
for fk in table.foreign_keys:
    print(f"ForeignKey: {fk}")
    print(f"  str: {fk!s}")
    print(f"  target_fullname: {fk.target_fullname}")
    print(f"  column.name: {fk.column.name}")
    print()