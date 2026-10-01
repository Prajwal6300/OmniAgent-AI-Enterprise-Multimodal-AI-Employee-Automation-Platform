#!/usr/bin/env python
"""
Generate Alembic initial migration from actual SQLAlchemy models.

This script reads the registered SQLAlchemy models from app/models/
and generates a proper Alembic migration file.
The model definitions are the source of truth - no assumptions made.
"""

import os

os.chdir(r"F:\Projects\OmniAgent AI — Enterprise Multimodal AI Employee & Automation Platform\backend")

# Set DATABASE_URL for reference
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/omniagent_db'

# Import all models to register them in Base.metadata
import app.models  # noqa - registers all 27 models
from app.db.base import Base

tables = sorted(Base.metadata.tables.keys())
print(f"Tables in Base.metadata: {len(tables)}")
for t in tables:
    print(f"  - {t}")

# Generate the migration file
migration_dir = os.path.join('migrations', 'versions')
os.makedirs(migration_dir, exist_ok=True)

# Check existing migration files
existing_files = [f for f in os.listdir(migration_dir) if f.endswith('.py') and f != '__init__.py']
print(f"\nExisting migration files: {existing_files}")

# Define the table creation order based on foreign key dependencies
table_dependency_order = [
    "organizations",        # no FK deps
    "departments",         # FK: organizations.id
    "roles",               # FK: organizations.id (nullable)
    "permissions",         # no FK deps
    "role_permissions",    # FK: roles.id, permissions.id (composite PK)
    "users",               # FK: organizations.id, departments.id, roles.id
    "integrations",        # FK: organizations.id
    "documents",           # FK: organizations.id, users.id
    "document_chunks",     # FK: documents.id, organizations.id
    "conversations",       # FK: organizations.id, users.id
    "messages",            # FK: conversations.id
    "agent_runs",          # FK: organizations.id, conversations.id, users.id
    "tool_calls",          # FK: agent_runs.id
    "approvals",           # FK: organizations.id, agent_runs.id, workflow_runs.id, users.id
    "audit_logs",          # FK: organizations.id, users.id
    "workflows",           # FK: organizations.id (index)
    "workflow_runs",       # FK: workflows.id, organizations.id
    "actions",             # FK: organizations.id, users.id
    "action_approvals",    # FK: actions.id, organizations.id, users.id
    "action_audit_logs",   # FK: organizations.id, users.id
    "machines",            # FK: organizations.id, departments.id
    "production_records",  # FK: machines.id, organizations.id
    "orders",              # FK: organizations.id
    "products",            # FK: organizations.id
    "vendors",             # FK: organizations.id
    "maintenance_requests",# FK: machines.id
    "notifications",       # FK: organizations.id, users.id
]

# Filter to only tables that exist in metadata
tables_to_migrate = [t for t in table_dependency_order if t in Base.metadata.tables]
print(f"\nTables to migrate: {len(tables_to_migrate)}")

# For each table, build the column definitions and FK references
# based on the actual SQLAlchemy Table objects from Base.metadata
table_specs = {}

for table_name in tables_to_migrate:
    table = Base.metadata.tables[table_name]
    
    # Build column definitions - each will be indented 8 spaces 
    # (4 for function body + 4 for inside op.create_table)
    columns = []
    fks = []
    
    for col in table.columns:
        # Build the column type string
        col_type_str = f"sa.{col.type}"
        
        # Add type-specific parameters
        if hasattr(col.type, 'precision') and col.type.precision is not None:
            if hasattr(col.type, 'scale') and col.type.scale is not None:
                col_type_str += f"({col.type.precision}, {col.type.scale})"
            else:
                col_type_str += f"({col.type.precision})"
        
        if hasattr(col.type, 'length') and col.type.length is not None:
            if not hasattr(col.type, 'precision') or col.type.precision is None:
                col_type_str += f"({col.type.length})"
        
        # Build column definition with 8-space indent (inside op.create_table)
        col_def_parts = [f"sa.Column('{col.name}', {col_type_str}"]
        
        if col.nullable:
            col_def_parts.append("nullable=True")
        else:
            col_def_parts.append("nullable=False")
        
        if col.primary_key:
            col_def_parts.append("primary_key=True")
        
        if col.default is not None:
            default_str = str(col.default)
            if 'Callable' in default_str:
                default_str = "sa.text('gen_random_uuid()')"
            col_def_parts.append(f"server_default={default_str}")
        
        if col.autoincrement:
            col_def_parts.append("autoincrement=True")
        
        # The full column definition with 8-space indent
        col_def = ", ".join(col_def_parts) + ","
        # Add 4 extra spaces to be inside op.create_table(
        columns.append("    " + col_def)  # 4 spaces + the col_def content
    
    # Add foreign key constraints
    for fk in table.foreign_keys:
        ref_table = fk.target_fullname.split('.')[0]  # e.g., "organizations.id" -> "organizations"
        ondelete = f"ondelete='{fk.ondelete}'" if fk.ondelete else "None"
        fk_def = f"    sa.ForeignKeyKey('{fk.column.name}', '{ref_table}', {ondelete})"
        fks.append(fk_def)
    
    table_specs[table_name] = {
        'columns': columns,
        'fks': fks,
    }

# Generate the migration code as a properly formatted string
# The upgrade() function is at module level (no leading indent)
# op.create_table( is at 4-space indent
# Columns and FKs inside are at 8-space indent

migration_lines = []

migration_lines.append("def upgrade():")
migration_lines.append("    # ### commands auto-generated by Alembic from actual SQLAlchemy models ###")
migration_lines.append("")

# Generate CREATE TABLE for each table in dependency order
for table_name in tables_to_migrate:
    specs = table_specs[table_name]
    
    migration_lines.append(f"    # {table_name}")
    migration_lines.append("    op.create_table(")
    migration_lines.append(f"        '{table_name}',")
    
    # Add column definitions (at 8-space indent from function start = 4 inside create_table)
    all_cols = "\n        ".join(specs['columns'])
    migration_lines.append(all_cols)
    
    # Add foreign key constraints (also at 8-space indent)
    all_fks = "\n        ".join(specs['fks'])
    if all_fks:
        migration_lines.append(all_fks)
    
    migration_lines.append("    )")
    migration_lines.append("")  # blank line between tables

# Add downgrade function - drop tables in reverse order
migration_lines.append("def downgrade():")
migration_lines.append("    # ### commands auto-generated by Alembic from actual SQLAlchemy models ###")
migration_lines.append("    # Tables dropped in reverse order of creation")
migration_lines.append("")

for table_name in reversed(tables_to_migrate):
    migration_lines.append(f"    op.drop_table('{table_name}')")

migration_lines.append("")
migration_lines.append("    # ### end Alembic commands ###")

# Write the migration file
migration_path = os.path.join(migration_dir, 'initial.py')
with open(migration_path, 'w') as f:
    f.write("\n".join(migration_lines))

print(f"\nMigration written to: {migration_path}")

# Verify the vector column
if 'document_chunks' in Base.metadata.tables:
    dc = Base.metadata.tables['document_chunks']
    for col in dc.columns:
        if 'embedding' in col.name.lower():
            print(f"\nVector column found: {col.name}")
            print(f"  Type: {col.type}")
            if hasattr(col.type, 'dim'):
                print(f"  Dimension: {col.type.dim}")

print("\nMigration generation complete!")