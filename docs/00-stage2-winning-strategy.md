# OpsPilot Stage 2 Upgrade Strategy

OpsPilot is being positioned for the Qwen Cloud Global AI Hackathon as a workflow-first backend agent, not a chat demo. This document explains how the current system fits Track 4, where it already has depth, and what still needs to be implemented to compete strongly in Stage 2.

## 1. Why OpsPilot fits Track 4: Autopilot Agent

OpsPilot fits Track 4 because it automates a real backend and SRE workflow end to end:

1. alert intake
2. incident creation
3. Qwen-powered triage
4. tool selection
5. logs, metrics, health, deployment, and runbook investigation
6. diagnosis
7. remediation recommendation
8. human approval for risky actions
9. safe simulated execution
10. final report
11. audit trail and timeline

This is not a chatbot flow where a user asks open-ended questions and the model answers freely. OpsPilot is a backend-controlled workflow agent with fixed orchestration, validated model outputs, an allowlisted tool surface, and explicit human approval gates.

## 2. Stage 1 pass/fail requirements

Stage 1 is mainly about baseline fit and viability. OpsPilot is aligned with those requirements as follows:

| Requirement | Status | Notes |
|---|---|---|
| Uses Qwen Cloud models | Implemented | `QwenProvider` and `QwenClient` support `qwen3.7-plus` through Qwen Cloud compatible-mode APIs. |
| Fits Track 4: Autopilot Agent | Implemented | The backend runs a real incident workflow with tools, approvals, and remediation simulation. |
| Has a working project | Implemented | FastAPI backend, database, dashboard, demo scenarios, and tests are in place. |
| Has public repo and license | Implemented locally | MIT `LICENSE` exists; public publishing is still a release step. |
| Has architecture diagram | Implemented in docs | Architecture documentation exists; a polished export for judges may still be helpful. |
| Has Alibaba Cloud deployment proof | To Implement fully | Deployment artifacts and proof template exist; live cloud deployment proof still needs to be captured. |
| Has demo video | To Implement | Demo script exists, but recording is still pending. |
| Has project description | Implemented in docs | README and supporting docs describe the project and workflow. |

## 3. Stage 2 scoring strategy

| Category | Weight | How OpsPilot should score |
|---|---:|---|
| Innovation & AI Creativity | 30% | Evidence-first reasoning, structured Qwen outputs, tool selection, incident memory, evaluation scenarios, and human approval policy show a workflow agent design rather than a chatbot wrapper. |
| Technical Depth & Engineering | 30% | FastAPI backend, service-layer architecture, agent orchestrator, tool registry, Qwen provider abstraction, Pydantic validation, workflow state handling, audit logs, approval service, SQLAlchemy models, tests, and Docker artifacts all contribute to real engineering depth. |
| Problem Value & Impact | 25% | Small teams rarely have 24/7 SRE coverage. Incident triage is repetitive, time-sensitive, and high stress. OpsPilot reduces investigation time while keeping humans in control of risky changes. |
| Presentation & Documentation | 15% | Dashboard, timeline, Swagger/OpenAPI, architecture docs, ERD-ready data model docs, deployment notes, and a short demo story make the workflow understandable to judges quickly. |

### Innovation & AI Creativity

Status:
- Implemented: evidence-backed triage, structured Qwen contracts, constrained tool usage, approval-aware remediation flow, incident memory retrieval, and deterministic scenario evals

### Technical Depth & Engineering

Status:
- Implemented: FastAPI backend, SQLAlchemy persistence, service layer, provider abstraction, tool registry, risk policy, approvals API, dashboard, integration tests, Docker artifacts
- To Implement: richer timeline step structure only

### Problem Value & Impact

Status:
- Implemented: workflow centered on backend alert triage, evidence gathering, diagnosis, safe remediation, and memory-assisted incident reuse

### Presentation & Documentation

Status:
- Implemented: README, architecture docs, dashboard, demo script, Qwen usage notes, deployment notes
- To Implement: live Alibaba Cloud proof capture, demo video, and Devpost submission draft

## 4. Core differentiation

OpsPilot is not:

- a chatbot
- a generic alert summarizer
- a free-form LLM wrapper
- a fake autonomous infrastructure bot

OpsPilot is:

- an evidence-first SRE autopilot
- a backend-controlled workflow agent
- a Qwen-powered reasoning system
- a tool-using incident investigator
- a human-approved remediation system
- an auditable incident timeline

## 5. Required differentiators

### Differentiator 1: Evidence-first timeline

Goal:

- alert received
- severity classified
- Qwen decision
- tools selected
- tool calls
- tool outputs
- diagnosis
- risk policy decision
- approval request
- approval or rejection
- remediation result
- final report
- memory saved

Current status:
- Implemented: incident creation is stored in audit logs; triage, tool selection, memory lookup, tool calls, diagnosis, remediation recommendation, risk-policy decisions, approval requests, remediation execution, final reports, and memory saved events are persisted and visible in the dashboard timeline
- To Implement: a fully normalized AgentStep structure with title and summary fields

Current storage note:
- Timeline evidence is currently split across `AgentStep`, `ApprovalRequest`, and `AuditLog`

### Differentiator 2: Backend risk policy engine

Risk levels:

- `safe`
- `medium`
- `dangerous`

Example actions:

- `generate_report` = `safe`
- `send_status_update` = `safe`
- `create_issue` = `safe`
- `scale_workers_simulation` = `medium`
- `restart_api_workers_simulation` = `dangerous`
- `rollback_deployment_simulation` = `dangerous`

Current status:
- Implemented: backend policy evaluation decides what can run, unknown actions are rejected, and dangerous actions require approval
- To Implement: additional action coverage such as queue clearing and feature-flag disabling

Hard rule:
- The model can recommend an action, but it cannot bypass backend policy

### Differentiator 3: Incident memory

Desired record:

- `incident_type`
- `symptoms`
- `tools_used`
- `root_cause`
- `successful_fix`
- `failed_fix`
- `confidence`
- `created_at`

Current status:
- Implemented: `IncidentMemory` records are saved after resolution, similar memories are retrieved before diagnosis, memory context is added to Qwen prompts, and memory usage is visible in the dashboard
- Future Work: vector embeddings can come later, but the MVP uses incident-type matching and keyword overlap

Demo goal:
- "This incident resembles a previous database connection exhaustion incident."

### Differentiator 4: Agent evaluation scenarios

Target scenarios:

- `high_api_error_rate`
- `queue_backlog`
- `database_latency`
- `ambiguous_alert`
- `tool_failure`

Current status:
- Implemented: deterministic scenario cases and PASS-style assertions exist in automated tests
- Implemented: dedicated evaluation API endpoints and a dashboard page surface PASS or FAIL results directly to a judge

Each scenario should define:

- expected severity
- expected tools
- expected approval requirement
- expected diagnosis category
- expected final status

### Differentiator 5: Structured Qwen output contracts

Required strict JSON shapes:

- triage output
- tool selection output
- diagnosis output
- remediation recommendation output
- final report output

Current status:
- Implemented: strict JSON contracts exist for triage, tool selection, diagnosis, remediation, and final report; Pydantic validation rejects invalid payloads and the agent falls back safely on timeout or invalid JSON

## 6. Updated project positioning

OpsPilot is an evidence-first SRE autopilot that uses Qwen Cloud, backend-controlled tools, incident memory, risk policies, and human approval to triage and safely remediate production incidents.

Current honesty note:
- Implemented now: Qwen Cloud, backend-controlled tools, incident memory, risk policies, human approval, timeline, dashboard, and eval tests

## 7. Updated demo story

1. User launches the `high_api_error_rate` scenario.
2. OpsPilot creates an incident.
3. Qwen classifies severity.
4. The agent selects tools from the allowlist.
5. The backend executes logs, metrics, health, deployment, and runbook tools.
6. Evidence shows DB connection exhaustion after a deployment.
7. Qwen generates a diagnosis with confidence.
8. The backend risk policy marks restart as dangerous.
9. An approval request is created.
10. The user approves the action.
11. Safe simulated remediation runs.
12. The incident status becomes resolved.
13. A final incident report is generated.
14. Incident memory is saved.
15. An evaluation view shows the scenario passed.

Current status of this exact story:
- Implemented through step 13, with one caveat: final reports are fully persisted for the direct safe-action path and simplified after approval execution
- Implemented: step 14 incident memory save
- Implemented: step 15 evaluation page or endpoint visible to the user

## 8. Implementation priority before Phase 10

These are the Stage 2 differentiators that matter most before treating the project as fully hackathon-ready:

| Priority | Status | Notes |
|---|---|---|
| AgentStep timeline | Partially Implemented | Timeline exists, but richer per-step structure is still needed. |
| Risk policy engine | Implemented | Unknown actions are rejected and risky actions require approval. |
| Structured Qwen schemas | Implemented | Triage, tool selection, diagnosis, remediation, and final report schemas exist, with safe fallback handling on provider or JSON failures. |
| Tool registry validation | Implemented | Allowlist, standard tool results, and unknown-tool rejection are in place. |
| Incident memory | Implemented | Memory is saved after resolution and retrieved before diagnosis using simple similarity scoring. |
| Evaluation scenarios | Implemented | Eval cases run through both tests and a user-visible dashboard/API evaluation runner. |
| Dashboard visibility for timeline, approval, and report | Implemented | Current dashboard shows those workflow pieces. |
| Docs updated to reflect this strategy | Implemented | This document, the upgrade plan, checklist, and refreshed supporting docs align the project story. |
