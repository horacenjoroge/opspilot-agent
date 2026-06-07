# Local Development Guide

## Prerequisites

- Python 3.13
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

The app currently initializes the SQLAlchemy tables automatically on startup. There is no migration framework in the repo yet.

## Running Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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
