# OmniAgent AI — Database Architecture & Specifications

This directory holds the raw relational database DDL schemas, Entity Relationship Diagrams (ERDs), and baseline seed scripts for **OmniAgent AI**.

## Database Engine
- **Engine**: PostgreSQL 16+
- **Extensions**:
  - `uuid-ossp` or `pgcrypto` for cryptographically secure UUID v4 generation.
  - `vector` (pgvector 0.7+) for dense HNSW similarity search indexing.

## Multi-Tenant Strategy
Every enterprise resource is strictly scoped to an `organization_id`. Database queries must append tenant filters or leverage PostgreSQL Row-Level Security (RLS) to ensure zero cross-tenant data leakage.

## Directory Structure
- `schema/schema.sql`: Complete production DDL script defining all tables, constraints, indexes, and pgvector HNSW indexes.
- `schema/erd.md`: Mermaid entity relationship diagram documenting all relationships.
- `seeds/seed_data.sql`: Seed data for bootstrapping organizations, roles, permissions, and system workflows.
- `migrations/`: High-level migration documentation. (Active migration scripts are managed via Alembic in `backend/migrations/`).
