# Database Notes

## Current Default

OpsPilot uses SQLite by default for local demos:

```env
DATABASE_URL=sqlite:///./opspilot.db
```

This keeps hackathon setup simple and preserves the seeded demo flow.

## Current Tables

- `incidents`
- `agent_steps`
- `approval_requests`
- `audit_logs`
- `incident_memories`
- `evaluation_runs`
- `evaluation_case_results`
- `users`
- `user_sessions`

## What Was Added In Database Phase 1

- persisted evaluation history
- safe composite indexes for incident timeline, approval, and audit query patterns
- minimal Alembic migration support

## What Was Added In Auth Phase 1

- `users` for local or production-backed identities
- `user_sessions` for revocable DB-backed sessions
- role structure for `admin`, `operator`, `reviewer`, and `viewer`
- SQLite-safe migration `0002_auth_foundation`

## Eval History

Each evaluation run now persists:

- run metadata such as provider, totals, pass/fail counts, and duration
- one row per scenario result

The current eval API remains compatible. Persistence is an additional side effect.

## Migrations

Alembic now exists under `backend/alembic`.

Useful commands:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
alembic downgrade -1
```

If your local SQLite file was created before Alembic and already contains OpsPilot tables, `alembic upgrade head` now bootstraps that unmanaged DB automatically when the schema is compatible, including additive column and index repair for legacy local tables.

## SQLite And `create_all()`

OpsPilot still keeps `Base.metadata.create_all()` for easy local bootstrap.

Use this when:

- you want a zero-friction local demo DB
- you are starting from a fresh local SQLite file

Prefer Alembic when:

- you want a reproducible schema history
- you are preparing for shared or deployed environments
- you need to add schema changes safely over time

## Postgres Later

Postgres is not required today, but the app can be pointed at a future Postgres database by changing `DATABASE_URL`.

Example future shape:

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/opspilot
```

## Intentionally Deferred

- actor identity model
- deployment metadata tables
- vector DB / embeddings
- real semantic memory engine
