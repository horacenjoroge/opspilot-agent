# Local Development Guide

## Prerequisites

- Python 3.11+
- `pip`
- Docker and Docker Compose for containerized local runs

## Clone Repo

```bash
git clone <repo-url>
cd opspilot-agent
```

## Backend Setup

```bash
cp .env.example .env
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Frontend Setup

There is no separate frontend package. The dashboard is served directly by FastAPI.

## `.env` Setup

Set at minimum:

```env
LLM_PROVIDER=mock
DATABASE_URL=sqlite:///./opspilot.db
```

Optional auth flags:

```env
ENABLE_AUTH=false
ENABLE_DASHBOARD_AUTH=false
AUTH_SESSION_COOKIE_NAME=opspilot_session
AUTH_SESSION_TTL_HOURS=24
```

## Mock Provider Mode

Recommended default for development:

```env
LLM_PROVIDER=mock
```

## Qwen Provider Mode

```env
LLM_PROVIDER=qwen
QWEN_API_KEY=your_key_here
QWEN_MODEL=qwen3.7-plus
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

## Database Setup

The app still initializes SQLAlchemy tables automatically on startup for easy local demos.

Alembic migrations now also exist for reproducible schema setup:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Recommended local rule of thumb:

- use `create_all()` behavior for quick disposable SQLite demo databases
- use Alembic when you want a repeatable schema setup or are preparing for deployment

## Running Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Seeding A Dev Admin

When auth is enabled locally, seed a database-backed admin user:

```bash
cd backend
source .venv/bin/activate
python -m app.scripts.seed_admin --email admin@opspilot.local --password change-me-now
```

## Running Frontend

Open the served dashboard after backend startup:

- `http://localhost:8000/`

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## Common Errors and Fixes

- `401 Unauthorized` from Qwen:
  check the key, base URL, workspace access, and model name
- live Qwen test skipped:
  set `QWEN_API_KEY` for that test run
- Docker build works but app not reachable:
  verify the Docker daemon is running and port `8000` is free

## How to Safely Test the Qwen API

- start with `MockProvider`
- use the live smoke test only when needed
- never commit the test key
- prefer the dashboard or one-off smoke test over wiring live Qwen into every local test run
