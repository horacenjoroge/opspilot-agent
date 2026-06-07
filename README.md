# OpsPilot

OpsPilot is an evidence-first SRE autopilot for incident triage and safe remediation.

Track: Track 4 — Autopilot Agent

OpsPilot helps small engineering teams respond to production alerts faster by combining Qwen Cloud reasoning, backend-controlled tools, human approval for risky actions, and a fully auditable incident timeline.

## Why It Matters

Incident triage is repetitive, time-sensitive, and easy to get wrong under pressure. Many teams do not have dedicated 24/7 SRE coverage, so they need automation that accelerates investigation without giving an LLM unsafe control over infrastructure.

## What OpsPilot Does

- receives or seeds incidents
- classifies severity and incident type with Qwen or a mock provider
- validates tool selection against an allowlist
- gathers evidence from logs, metrics, health, deployments, and runbooks
- generates a diagnosis and remediation recommendation
- applies a backend risk policy
- requires human approval for dangerous actions
- simulates remediation safely
- saves audit logs, agent steps, approvals, and incident memory
- produces final reports and evaluation results

## Core Demo Flow

1. Create a demo incident such as `high_api_error_rate`.
2. Run the agent from the dashboard or API.
3. Review Qwen classification, selected tools, and gathered evidence.
4. See the diagnosis and recommended remediation.
5. Approve the risky action if required.
6. Watch the simulated remediation complete.
7. Inspect the final report, incident memory, and evaluation results.

## Feature List

- FastAPI backend with thin routes and service-layer architecture
- incident CRUD API and timeline API
- Qwen provider abstraction with `MockProvider` and `QwenProvider`
- strict JSON prompt contracts validated by Pydantic
- tool registry with allowlisted investigation and action tools
- backend risk policy engine with approval gating
- human-in-the-loop approval workflow
- incident memory retrieval and save-on-resolution
- built-in browser dashboard
- deterministic evaluation runner with PASS/FAIL output
- Docker Compose local run and production-shaped deployment artifacts

## Architecture Summary

- dashboard: FastAPI-rendered HTML plus lightweight JS
- backend API: incidents, approvals, demo scenarios, evaluations, health
- agent orchestrator: controlled workflow loop with max-step limit
- Qwen integration: provider abstraction and client with timeout/retry handling
- tool system: allowlisted evidence and remediation tools
- persistence: incidents, agent steps, approvals, audit logs, incident memory
- deployment: Docker and Nginx artifacts for Alibaba Cloud ECS-style hosting

See:
- [docs/architecture-comprehensive.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/architecture-comprehensive.md:1)
- [docs/architecture-diagram.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/architecture-diagram.md:1)
- [docs/database-erd-design.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/database-erd-design.md:1)

## Tech Stack

- Python 3.13
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- httpx
- pytest
- Docker / Docker Compose
- Nginx
- Qwen Cloud compatible-mode API

## How Qwen Cloud Is Used

Qwen is used for:
- alert classification
- tool-plan generation
- diagnosis generation
- remediation recommendation
- final report generation

All Qwen responses used by the backend must be strict JSON and are validated by Pydantic schemas before the workflow uses them. If Qwen times out or returns invalid JSON, OpsPilot falls back to a safe backend-controlled path.

See [docs/qwen-cloud-usage.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/qwen-cloud-usage.md:1).

## How the Agent Uses Tools

The model does not execute infrastructure actions directly. It can only recommend allowlisted tools. The backend validates tool names, executes the tools, stores results in the timeline, and rejects unknown tools.

Implemented tools:
- `logs_tool`
- `metrics_tool`
- `health_tool`
- `deployment_tool`
- `runbook_tool`
- `remediation_tool`
- `notification_tool`

See [docs/tool-system.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/tool-system.md:1).

## Human-In-The-Loop Safety Model

- `safe` actions may execute directly
- `medium` actions are approval-gated by configuration in this MVP
- `dangerous` actions always require approval
- unknown actions are rejected
- the model cannot bypass policy

See [docs/human-in-the-loop.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/human-in-the-loop.md:1).

## API and Swagger

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

Full API reference:
- [docs/api.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/api.md:1)

## Local Setup

```bash
cp .env.example .env
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or from the repo root:

```bash
docker compose up --build
```

## Environment Variables

Core variables:

```env
APP_NAME=opspilot
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=sqlite:///./opspilot.db
LLM_PROVIDER=mock
REQUIRE_APPROVAL_FOR_MEDIUM_RISK=true
QWEN_API_KEY=
QWEN_MODEL=qwen3.7-plus
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

## Running the Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running the Frontend

There is no separate SPA frontend. The dashboard is served by FastAPI with Jinja templates and static assets.

Dashboard routes:
- `/`
- `/incidents`
- `/incidents/{id}`
- `/approvals`
- `/demo`
- `/evals`

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Current test result at the time of this update:
- `43 passed, 1 skipped`

The skipped test is the optional live Qwen smoke test when `QWEN_API_KEY` is not set for that run.

## Deployment Notes

- local development stack: `docker-compose.yml`
- production-shaped stack: `deployment/docker-compose.prod.yml`
- reverse proxy config: `deployment/nginx.conf`
- target hosting shape: Alibaba Cloud ECS

See:
- [docs/deployment-guide.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/deployment-guide.md:1)
- [deployment/alibaba-cloud.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/deployment/alibaba-cloud.md:1)

## Alibaba Cloud Proof

The repository includes production-oriented deployment artifacts and a proof template, but a live public ECS proof URL still needs to be captured for final submission.

See [deployment/alibaba-cloud.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/deployment/alibaba-cloud.md:1).

## Demo Video / Script

- demo script: [docs/demo-script.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/demo-script.md:1)
- Devpost draft: [docs/devpost-submission.md](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/docs/devpost-submission.md:1)

## Honest Status

Implemented:
- backend workflow agent
- tool allowlisting
- approval gating
- incident memory
- evaluation runner
- dashboard
- Swagger/OpenAPI documentation

Future Work:
- live public Alibaba Cloud proof URL
- final demo video
- final Devpost links and published repo URL
- migration tooling
- Prometheus/Grafana/Sentry integration

## License

This project is licensed under the MIT License. See [LICENSE](/Users/la/Desktop/Repository/horacenjoroge/opspilot-agent/LICENSE:1).
