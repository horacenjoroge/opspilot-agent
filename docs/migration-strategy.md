# Migration Strategy

Current status: Implemented for Phase 1

OpsPilot now includes a minimal Alembic setup in `backend/alembic` while still preserving `Base.metadata.create_all()` for easy local SQLite demos.

## Current Migration Commands

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
alembic downgrade -1
```

## How To Use It Safely

- use `create_all()` for disposable local demo databases
- use Alembic for reproducible schema setup and future schema changes
- prefer additive migrations first
- review schema diffs before applying them
- test migrations against SQLite before deployment

## Existing SQLite Demo Databases

If you already created a local SQLite DB with `create_all()`, you have two safe options:

- start from a fresh local DB file and run `alembic upgrade head`
- keep the existing DB and run `alembic upgrade head`

The second path now works for schema-compatible local demo DBs too:

- Alembic detects an existing unmanaged SQLite DB that already has OpsPilot tables
- it creates any fully missing modeled tables
- it adds missing additive columns and indexes for legacy SQLite demo tables
- it stamps the DB to the current Alembic head
- then future migrations can proceed normally

This is meant for local/demo databases that were bootstrapped before Alembic existed. For production-style environments, prefer running migrations from the beginning on a clean database.

## Postgres Later

The migration setup is intentionally simple and keeps SQLite working. A future Postgres deployment can reuse the same Alembic workflow by changing `DATABASE_URL`.
