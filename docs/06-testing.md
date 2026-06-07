# Testing Strategy

## Test Matrix

| Category | Focus | Expected Outcome |
|---|---|---|
| Unit tests | Schemas, services, registry, policies | Fast validation of core backend rules |
| Integration tests | API plus agent workflow | End-to-end lifecycle works with mock provider |
| Agent evaluation tests | Deterministic scenarios | Same alerts produce the expected tools and actions |
| Failure tests | Tool errors, bad model JSON, timeouts | System fails safely and records the error |
| Safety/security tests | Unknown tools, risky actions, approval rejection | Unsafe behavior is blocked |

## Demo Scenarios

### High API Error Rate

- Expected severity: `high` or `critical`
- Expected tools: `logs_tool`, `metrics_tool`, `health_tool`, `deployment_tool`, `runbook_tool`
- Expected behavior: detect DB connection exhaustion or similar backend failure evidence

### Queue Backlog

- Expected tools: `metrics_tool`, `health_tool`, `runbook_tool`
- Expected behavior: identify worker saturation or processing lag

### Database Latency Spike

- Expected tools: metrics plus logs and runbook context
- Expected behavior: surface DB latency evidence and recommend a bounded response

### Ambiguous Alert

- Expected behavior: start with broad, safe investigation tools rather than risky remediation

### Tool Failure

- Expected behavior: record the failure, avoid crashing the whole workflow, and continue or stop safely

## Evaluation Scenarios

OpsPilot uses deterministic seeded cases to show that the backend workflow produces repeatable outcomes instead of ad hoc chat replies.

Tracked scenarios:

- `high_api_error_rate`
- `queue_backlog`
- `database_latency`
- `ambiguous_alert`
- `tool_failure`

Current status:

- Implemented: scenario definitions, expected outputs, automated PASS-style evaluation tests, API evaluation endpoints, and a dashboard evaluation page

## Mock LLM Strategy

- Tests use `MockProvider` by default.
- Mock responses stay deterministic so agent workflow tests are stable.
- Live Qwen calls should be opt-in only and isolated from normal CI.

## Foundation Tests in This Phase

Phase 2 only adds the backend health check test to verify the app boots and reads configuration correctly. Broader agent and safety tests come later in the build order.

## Current Results

Current automated coverage includes:

- unit tests for schemas, services, audit logging, risk policy, registry, tools, approvals, and dashboard rendering
- an agent loop test suite for happy path, tool failure handling, unknown tool rejection, and `max_steps` enforcement
- a full workflow integration test:
  `create incident -> run agent -> approval request -> approve -> remediation -> final report`
- incident memory tests that verify resolved incidents are saved and similar incidents retrieve prior memory
- runnable eval cases for:
  `high_api_error_rate`, `queue_backlog`, `database_latency`, `ambiguous_alert`, and `tool_failure`

Observed expected behavior by scenario:

| Scenario | Expected Severity | Expected Tools | Approval Behavior | Diagnosis Keywords |
|---|---|---|---|---|
| `high_api_error_rate` | `high` | `logs_tool`, `metrics_tool`, `health_tool`, `deployment_tool`, `runbook_tool` | approval required | `database`, `connection`, `exhaustion` |
| `queue_backlog` | `high` | `metrics_tool`, `health_tool`, `runbook_tool` | approval required | `queue`, `workers`, `saturated` |
| `database_latency` | `high` | `metrics_tool`, `logs_tool`, `runbook_tool` | no approval required | `database`, `latency`, `slow` |
| `ambiguous_alert` | `medium` | `logs_tool`, `metrics_tool`, `health_tool`, `runbook_tool` | no approval required | `ambiguous`, `inconclusive`, `investigation` |
| `tool_failure` | `medium` | `logs_tool`, `health_tool` | no approval required | `incomplete`, `failed`, `fallback` |

## Expected Vs Actual Results

The current evaluation runner compares:

- expected severity against the triage output
- expected tools against the tool list returned by the provider
- expected approval behavior against the remediation decision
- expected diagnosis keywords against the diagnosis output

Current result status:

- Implemented: automated assertions are passing for the seeded scenarios under `MockProvider`
- Implemented: the dashboard and API expose a public-facing PASS or FAIL summary outside raw pytest output

## PASS/FAIL Summary

At the time of this documentation update:

- Implemented: evaluation tests pass in the automated suite
- Implemented: integration workflow passes from incident creation through approval and report generation
- Implemented: a judge-visible evaluation page and API endpoint exist at `/evals` and `/api/evals/run`

## Failure Cases

The system is also tested for failure-oriented behaviors:

- unknown tools are rejected safely
- tool failures are captured without crashing the workflow
- `max_steps` prevents runaway loops
- approval rejection blocks execution

Current important gap:

- Implemented: explicit incident-agent fallback behavior for live Qwen timeout or invalid JSON errors

The backend test suite continues to use `MockProvider` by default. Live Qwen verification remains isolated to the optional smoke test and is skipped unless `QWEN_API_KEY` is explicitly provided.
