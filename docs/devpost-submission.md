# Devpost Submission Draft

## Project Title

OpsPilot

## Tagline

An evidence-first SRE autopilot for safe incident triage and remediation with Qwen Cloud.

## Track

Track 4 — Autopilot Agent

## Inspiration

Incident response is repetitive, stressful, and time-sensitive. Small engineering teams often lack 24/7 SRE coverage, which means on-call developers manually triage alerts across fragmented dashboards, logs, metrics, and runbooks under pressure. We wanted to build an agent that behaves more like a backend SRE workflow system than a chatbot — one that accelerates investigation while keeping humans firmly in control of dangerous infrastructure changes.

## What It Does

OpsPilot receives production incidents, uses Qwen Cloud for structured reasoning across four workflow stages, investigates evidence through an allowlisted tool registry, applies a backend risk policy, requires human approval for dangerous actions, simulates safe remediation, records a fully auditable evidence timeline, and saves reusable incident memory to improve future diagnosis context.

Key capabilities:
- five seeded demo scenarios covering API error rate, queue backlog, database latency, ambiguous alerts, and tool failure
- Qwen-backed triage, diagnosis, remediation recommendation, and final report generation
- eight-action remediation catalog with safe, medium, and dangerous risk tiers
- human approval gate for medium and dangerous actions
- incident memory retrieval before diagnosis to surface similar past incidents
- evaluation runner with PASS/FAIL scoring visible from the dashboard
- evidence-first timeline showing every agent decision as a labelled card

## How It Works

- FastAPI backend orchestrates a fixed workflow loop with a max-step limit
- Qwen Cloud returns strict JSON for each reasoning stage; the backend validates every response with Pydantic before acting
- tool registry executes only allowlisted investigation tools: logs, metrics, health, deployment, and runbook
- backend risk policy classifies each recommended action independently of the model
- approval service gates medium and dangerous actions behind a human decision
- incident memory retrieves similar past incidents and injects context into the diagnosis prompt
- evaluation runner runs all five scenarios and scores severity, tool selection, approval behavior, and diagnosis keywords
- request ID middleware traces every request end to end
- optional session-based auth with role-based access (admin, operator, reviewer, viewer)

## How Qwen Cloud Is Used

Qwen Cloud is the sole reasoning engine across four structured JSON calls per incident run:

1. **Triage** — classifies severity, incident type, and recommends tools from the backend allowlist
2. **Diagnosis** — generates root cause summary and confidence score from collected evidence
3. **Remediation** — recommends a safe action from the approved action catalog
4. **Final report** — produces a structured incident summary with follow-up items

All Qwen outputs are strict JSON validated by Pydantic schemas. If the model times out, returns invalid JSON, or recommends an unknown tool, OpsPilot falls back to a safe backend-controlled path and logs the failure. The model never executes actions directly.

## How Alibaba Cloud Is Used

The deployment target is Alibaba Cloud ECS. Docker Compose and Nginx reverse proxy artifacts are included in the repo under `deployment/`. The production-shaped stack runs the FastAPI backend behind Nginx with HTTPS support. Live public proof URL to be attached for final submission.

## Built With

- Python 3.11
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Alembic
- httpx
- pytest
- Docker / Docker Compose
- Nginx
- Qwen Cloud compatible-mode API
- Alibaba Cloud ECS

## Challenges

- Keeping the system safe enough to be production-aware without building real infrastructure integrations
- Preventing the model from recommending arbitrary tool names or bypassing the backend risk policy
- Making the full workflow visible and scannable for judges through the evidence timeline
- Balancing a complete workflow agent with a demo-friendly local setup that requires no external services

## Accomplishments

- Built a real backend workflow agent with fixed orchestration, not a free-form chat wrapper
- Structured Qwen output contracts validated at every stage before the backend acts
- Tool registry allowlist that hard-fails on unknown model recommendations
- Human approval and backend risk policy that the model cannot bypass
- Incident memory retrieval and save-on-resolution for context-aware diagnosis
- Evaluation runner with PASS/FAIL scoring across five deterministic scenarios
- Evidence-first timeline with labelled cards showing every agent decision
- Session-based auth with role-based access for production-shaped demo environments
- 65+ passing tests including auth, request tracing, feature flags, and integration workflow

## What I Learned

- Workflow control and output validation matter as much as model quality in production agent systems
- Structured JSON contracts with Pydantic validation make agent behavior predictable and testable
- Evaluation visibility explains agent quality to judges faster than code review alone
- Keeping humans in the approval loop for dangerous actions is both safer and more compelling to demonstrate

## What's Next

- Live Alibaba Cloud proof URL (deployment in progress)
- Final demo video
- Devpost asset links
- Prometheus metrics endpoint for richer observability
- Embedding-backed incident memory for stronger similarity retrieval

## Testing Instructions

```bash
cp .env.example .env
# set LLM_PROVIDER=mock for local tests (no API key needed)
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

Or with Docker:

```bash
docker compose up --build -d
docker compose exec backend python -m app.scripts.seed_admin \
  --email admin@opspilot.local --password change-me-now
# open http://localhost:8000
```

## Demo Credentials

When `ENABLE_AUTH=true` (Docker default):

```
Email:    admin@opspilot.local
Password: change-me-now
```

Seed with:
```bash
docker compose exec backend python -m app.scripts.seed_admin \
  --email admin@opspilot.local --password change-me-now
```

## Required Links Checklist

- GitHub repo: https://github.com/horacenjoroge/opspilot-agent
- Live demo: TODO — Alibaba Cloud ECS deployment in progress
- Demo video: TODO — to be recorded after live deployment
- Architecture diagram: present in `docs/architecture-diagram.md`
- Alibaba Cloud proof: present as template in `deployment/alibaba-cloud.md`
- Blog/social post: optional, TODO if available
