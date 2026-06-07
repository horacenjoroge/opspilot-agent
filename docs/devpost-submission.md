# Devpost Submission Draft

## Project Title

OpsPilot

## Tagline

An evidence-first SRE autopilot for safe incident triage and remediation with Qwen Cloud.

## Track

Track 4 — Autopilot Agent

## Inspiration

Incident response is repetitive, stressful, and time-sensitive. We wanted to build an agent that behaves more like a backend SRE workflow system than a chatbot.

## What It Does

OpsPilot receives incidents, uses Qwen Cloud for structured reasoning, investigates evidence through allowlisted tools, applies a backend risk policy, requires human approval for dangerous actions, simulates remediation, records an auditable timeline, and saves reusable incident memory.

## How It Works

- FastAPI backend orchestrates the workflow
- Qwen or mock provider returns strict JSON
- backend validates outputs with Pydantic
- tool registry executes only allowlisted tools
- approval service gates risky actions
- incident memory improves future diagnosis context
- evaluation runner shows PASS/FAIL across seeded scenarios

## How Qwen Cloud Is Used

Qwen is used for classification, tool planning, diagnosis, remediation recommendation, and final report generation. All outputs are validated before the backend acts on them.

## How Alibaba Cloud Is Used

The deployment target is Alibaba Cloud ECS, with Docker and optional Nginx reverse proxy artifacts included in the repo. Final public proof and live URL still need to be attached for submission.

## Built With

- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- httpx
- pytest
- Docker
- Nginx
- Qwen Cloud
- Alibaba Cloud ECS

## Challenges

- keeping the system safe enough to look production-aware
- preventing the model from acting like an unrestricted automation bot
- making the workflow visible and auditable for judges

## Accomplishments

- built a real backend workflow agent, not just a chat wrapper
- added human approval and risk policy controls
- implemented incident memory and evaluation scenarios
- exposed a judge-friendly dashboard and OpenAPI surface

## What I Learned

- workflow control matters as much as model quality
- structured outputs and backend validation are essential for trustworthy agent behavior
- evaluation visibility helps explain agent quality much faster than raw code alone

## What’s Next

- live Alibaba Cloud proof URL
- final demo video
- Devpost asset links
- migration tooling
- richer observability

## Testing Instructions

```bash
cd backend
source .venv/bin/activate
pytest
```

## Demo Credentials

No login is implemented in the current local demo.

## Required Links Checklist

- GitHub repo: TODO
- Live demo: TODO
- Demo video: TODO
- Architecture diagram: present in `docs/architecture-diagram.md`
- Alibaba Cloud proof: present as template in `deployment/alibaba-cloud.md`
- Blog/social post: optional, TODO if available
