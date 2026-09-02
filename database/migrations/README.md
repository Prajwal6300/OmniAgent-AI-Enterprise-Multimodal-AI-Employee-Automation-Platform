# Database Migrations

OmniAgent AI leverages Alembic for declarative schema migrations.

## Location of Alembic Files
All migration definitions are maintained under `backend/migrations/` to keep Python SQLAlchemy model declarations and migration execution scripts unified within the backend service environment.

## Running Migrations
```bash
cd backend
alembic upgrade head
```

## Creating New Migrations
```bash
cd backend
alembic revision --autogenerate -m "describe_change"
```
