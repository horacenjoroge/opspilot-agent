# OpsPilot

OpsPilot is a Qwen-powered Autopilot Agent for incident triage and safe remediation, built for **Track 4: Autopilot Agent**.

This repository currently contains the project foundation: architecture and product docs, a FastAPI backend, incident persistence, a provider abstraction for mock and Qwen-backed LLM calls, strict JSON prompt contracts, Docker Compose support, and a growing backend test suite. The next phases will add the tool registry, approvals workflow endpoints, and the controlled incident agent loop.

## Current Scope

- Documentation-first project setup
- FastAPI backend skeleton
- SQLite-backed incident data model and service layer
- Environment-driven settings with mock provider default
- Mock and Qwen provider abstraction
- Strict JSON prompt and parser contracts for agent outputs
- `/health` readiness endpoint
- Incident CRUD API with audit logging
- Allowlisted tool registry with seeded investigation and action tools
- Risk policy and approval workflow endpoints
- Controlled incident agent loop with demo scenarios and timeline output
- Built-in browser dashboard for incidents, approvals, and demo flows
- Full integration test and runnable scenario eval coverage
- Docker Compose local startup
- Basic backend test coverage

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

The backend will be available at `http://localhost:8000`, and `GET /health` should return service status plus the configured LLM provider.

Current incident endpoints:

- `POST /api/incidents`
- `GET /api/incidents`
- `GET /api/incidents/{id}`
- `PATCH /api/incidents/{id}/status`
- `POST /api/incidents/{id}/run-agent`
- `GET /api/incidents/{id}/timeline`
- `GET /api/approvals`
- `GET /api/approvals/{id}`
- `POST /api/approvals/{id}/approve`
- `POST /api/approvals/{id}/reject`
- `POST /api/demo/incidents/{scenario_name}`

Current backend tool surface:

- `logs_tool`
- `metrics_tool`
- `health_tool`
- `deployment_tool`
- `runbook_tool`
- `remediation_tool`
- `notification_tool`

Browser dashboard routes:

- `/`
- `/incidents`
- `/incidents/{id}`
- `/approvals`
- `/demo`

Production deployment artifacts:

- `deployment/docker-compose.prod.yml`
- `deployment/nginx.conf`
- `deployment/alibaba-cloud.md`

## Local Development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Qwen Setup

Use the mock provider by default:

```env
LLM_PROVIDER=mock
```

Switch to Qwen Cloud for the final demo:

```env
LLM_PROVIDER=qwen
QWEN_API_KEY=your_key_here
QWEN_MODEL=qwen3.7-plus
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

Qwen calls are isolated to `backend/app/services/qwen_client.py` and `backend/app/llm/qwen_provider.py`. Tests use the mock provider by default, and there is an optional live smoke test in `backend/tests/test_qwen_client.py` that only runs when `QWEN_API_KEY` is set.

Use the base URL that matches the key type:

- Pay-as-you-go: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- Token Plan: `https://token-plan.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1`
- Coding Plan: `https://coding-intl.dashscope.aliyuncs.com/compatible-mode/v1`

## Project Layout

```txt
backend/     FastAPI backend foundation
docs/        product, architecture, and delivery docs
deployment/  deployment artifacts for later phases
```

## Safety Direction

- Routes stay thin and business logic belongs in services.
- Qwen calls will go through a provider abstraction.
- Model outputs will be strict JSON and validated.
- Dangerous actions will require human approval.
- All decisions and tool calls will be auditable.

## License

This project is licensed under the MIT License.
