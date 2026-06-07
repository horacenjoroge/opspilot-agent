# OpsPilot Stage 2 Implementation Upgrade Plan

This plan upgrades OpsPilot from a solid backend incident agent into a stronger Stage 2 submission. It is ordered to keep the implementation honest and focused on differentiators that judges can see quickly.

## Phase A: Evidence-first timeline

Implement or verify:

- `AgentStep` model and table
- each step has:
  - `incident_id`
  - `step_number`
  - `step_type`
  - `title`
  - `summary`
  - `tool_name`
  - `input_json`
  - `output_json`
  - `model_json`
  - `status`
  - `created_at`
- every agent action creates a timeline step
- dashboard can display timeline

Current status:
- Implemented: `AgentStep` table, step numbering, type, tool name, input and output JSON, status, timeline display
- Partially Implemented: summary currently exists as `model_summary`
- Implemented: explicit tool-selection, risk-policy, and memory-saved steps
- To Implement: explicit `title`, explicit `summary`, and explicit `model_json`

Acceptance criteria:

- creating an incident creates first timeline step
- running triage creates Qwen step
- tool calls create tool steps
- diagnosis creates model step
- approval creates approval step
- remediation creates remediation step
- final report creates report step

## Phase B: Risk policy engine

Implement or verify:

- `policies.py` or equivalent
- action risk map
- `safe`, `medium`, and `dangerous` risk levels
- dangerous actions create `ApprovalRequest`
- safe actions can execute directly
- unknown actions are rejected
- model cannot override risk policy

Current status:
- Implemented: policy module, action risk map, approval requirement logic, unknown action rejection, approval execution flow
- To Implement: explicit timeline event for policy decision and broader action catalog coverage

Acceptance criteria:

- rollback action always requires approval
- restart API action always requires approval
- generate report does not require approval
- rejected approval does not execute
- approved action executes simulation

## Phase C: Structured Qwen output contracts

Implement or verify Pydantic schemas for:

- `TriageDecision`
- `ToolSelectionDecision`
- `DiagnosisResult`
- `RemediationRecommendation`
- `FinalIncidentReport`

Current status:
- Implemented: `TriageDecision`, diagnosis, remediation, and final report schemas with required fields
- Implemented: a separate `ToolSelectionDecision`
- Implemented: agent-level fallback responses when Qwen times out or returns invalid JSON

Acceptance criteria:

- valid model JSON parses
- invalid JSON fails safely
- missing fields fail safely
- fallback response is created when Qwen fails

## Phase D: Tool registry validation

Implement or verify:

- base `Tool` interface
- tool registry
- allowed tool names
- unknown tool rejection
- standardized `ToolResult`
- tool risk level
- error handling

Current status:
- Implemented: shared base tool, registry, allowlist execution, standardized `ToolResult`, per-tool risk level, tool failure capture

Acceptance criteria:

- allowed tool executes
- unknown tool fails safely
- tool failure is stored as an `AgentStep`
- agent continues where possible after tool failure

## Phase E: Incident memory

Implement or verify:

- `IncidentMemory` model and table
- save memory after resolved incident
- retrieve similar memories before diagnosis
- include memory context in Qwen prompt

MVP similarity can be simple:

- keyword matching
- incident type matching
- symptom overlap

Future Work:
- vector embeddings and semantic retrieval

Current status:
- Implemented: `IncidentMemory` model, save-on-resolution flow, similar-memory retrieval before diagnosis, prompt injection, dashboard visibility, and timeline visibility
- Future Work: improve similarity scoring and add embedding-backed retrieval

Acceptance criteria:

- resolved incident saves memory
- new similar incident retrieves previous memory
- dashboard or timeline shows memory used
- Qwen prompt includes memory context

## Phase F: Agent evaluation scenarios

Implement:

- demo scenarios
- expected outputs
- evaluation runner

Scenarios:

1. `high_api_error_rate`
2. `queue_backlog`
3. `database_latency_spike`
4. `ambiguous_alert`
5. `tool_failure`

For each scenario define:

- input alert
- seeded logs
- seeded metrics
- expected severity
- expected tools
- expected approval behavior
- expected diagnosis type
- expected final state

Current status:
- Implemented: seeded scenarios, expected outputs, runnable evaluation tests
- Implemented: user-visible evaluation runner surface through dashboard and API
- To Implement: scenario naming cleanup so `database_latency_spike` matches the public docs

Acceptance criteria:

- evaluation can run all scenarios
- output shows PASS or FAIL
- result can be shown in dashboard or endpoint
- docs explain evaluation method

## Phase G: Dashboard upgrade

If frontend exists, update it. If frontend does not exist, create a simple one.

Required dashboard views:

- incident list
- incident detail
- timeline
- tool calls
- diagnosis
- approval request
- approve and reject buttons
- final report
- memory used
- evaluation results

Current status:
- Implemented: incident list, incident detail, timeline, approval queue, approve and reject buttons, final report, memory-used panel, and demo launcher
- Implemented: evaluation results view

Acceptance criteria:

- demo can be recorded without Postman
- judge can visually understand the workflow
- frontend does not need complex styling

## Phase H: Documentation alignment

After implementation, update:

- `README.md`
- `docs/00-stage2-winning-strategy.md`
- `docs/implementation-upgrade-plan.md`
- `docs/03-agent-design.md`
- `docs/04-tool-system.md`
- `docs/05-human-in-the-loop.md`
- `docs/06-testing.md`
- `docs/08-demo-script.md`
- `docs/devpost-submission.md`

Current status:
- Implemented now: README plus the main Stage 2 strategy, upgrade plan, testing, tool, approval, and demo docs have been refreshed
- To Implement: `docs/devpost-submission.md` once that file is created for final submission packaging
