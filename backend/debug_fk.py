import os
os.chdir(r"F:\Projects\OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform\backend")

from app.db.base import Base
import app.models  # noqa

table = Base.metadata.tables['users']
for fk in table.foreign_keys:
    print(f"ForeignKey: {fk}")
    print(f"  str: {str(fk)}")
    print(f"  target_fullname: {fk.target_fullname}")
    print(f"  column.name: {fk.column.name}")
    print()