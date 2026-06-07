# Agent Design

## Controlled Loop

OpsPilot is not a free-form chat agent. It follows a fixed backend workflow:

1. Load the incident and mark it as active for triage.
2. Ask Qwen for structured triage output with severity, incident type, recommended tools, and a short reasoning summary.
3. Validate the returned tool names against the backend allowlist.
4. Execute only approved tools through the tool registry.
5. Persist each tool call, input, output, and status in the timeline.
6. Send collected evidence back to Qwen for diagnosis.
7. Ask Qwen for a remediation recommendation in strict JSON.
8. Apply backend risk policy to the recommended action.
9. Execute safe actions immediately or create an approval request for risky actions.
10. Generate and persist a final incident report when the workflow is complete.

## Evidence-First Agent Loop

The agent is designed to reason over evidence, not to improvise. The intended loop is:

1. receive alert or demo scenario
2. create incident and record the initial timeline event
3. ask Qwen for structured triage output
4. validate the tool list against the allowlist
5. execute read-only evidence tools
6. store tool input, output, summary, and status
7. ask Qwen for structured diagnosis output
8. ask Qwen for structured remediation output
9. apply backend risk policy
10. execute safe actions or create approval requests
11. generate a final report
12. save incident memory for future similar incidents

Current status:

- Implemented: steps 1 through 12 including explicit tool-selection and stored risk-policy decisions

## Max Steps

The orchestration loop must enforce a hard `max_steps` limit so the agent cannot recurse or fan out indefinitely. If the limit is reached, the workflow should stop safely and record that the loop terminated early.

## Qwen Structured Output Contracts

- Every model response must be strict JSON.
- Every JSON payload must be validated with Pydantic schemas.
- Invalid or partial outputs must fail safely and be recorded for debugging.

Current implemented schemas:

- `TriageDecision`
- `ToolSelectionDecision`
- `DiagnosisDecision`
- `RemediationDecision`
- `FinalReportDecision`

Implemented safety behavior:

- an explicit `ToolSelectionDecision` schema
- agent-level fallback output when Qwen times out or returns invalid JSON

## Tool Selection And Allowlist

The model can only recommend tool names that exist in the registry. Unknown tools are rejected before execution and treated as a policy violation rather than a fallback to arbitrary behavior.

## Model Output Validation

Validation happens in two layers:

1. the provider and client require structured JSON responses
2. the parser validates required fields and rejects unknown tools before execution

This keeps route handlers thin and moves workflow safety into backend services and agent orchestration.

## Memory Retrieval

Target design:

- before diagnosis, retrieve similar past incident memories
- pass them into the Qwen context
- allow the agent to explain when a new incident resembles a previous one

Current status:

- Implemented: similar incident memories are retrieved before diagnosis, added to the Qwen prompt context, shown in the incident detail page, and saved again after resolution
- Future Work: move from keyword and incident-type matching to stronger embedding-based similarity

## Final Report Generation

The agent should finish with a concise final incident report that captures:

- what happened
- what evidence was collected
- what action was taken
- whether approval was required
- what follow-up items remain

Current status:

- Implemented for both the direct safe-action path and the approval path, with explicit final-report timeline steps persisted in each flow

## Failure Handling

Failure behavior must stay safe and auditable:

- unknown tools are rejected
- unknown actions are rejected by policy
- tool failures are captured as structured results
- `max_steps` stops runaway loops
- approval rejection blocks execution
- invalid model payloads fail the workflow safely

Current status:

- Implemented: live Qwen timeout and invalid-JSON failures now fall back to safe backend-owned triage, diagnosis, remediation, and final-report responses

## Approval Rules

- `safe` actions may run immediately.
- `medium` actions should require approval for the MVP unless config changes that policy later.
- `dangerous` actions must always require human approval.
- Rejected actions must never execute.

## Persistence Requirements

Each step must be auditable: the model decision, chosen tools, validation result, approval state, and final outcome all belong in the timeline record.
