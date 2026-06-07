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

## Max Steps

The orchestration loop must enforce a hard `max_steps` limit so the agent cannot recurse or fan out indefinitely. If the limit is reached, the workflow should stop safely and record that the loop terminated early.

## JSON Contracts

- Every model response must be strict JSON.
- Every JSON payload must be validated with Pydantic schemas.
- Invalid or partial outputs must fail safely and be recorded for debugging.

## Tool Allowlist

The model can only recommend tool names that exist in the registry. Unknown tools are rejected before execution and treated as a policy violation rather than a fallback to arbitrary behavior.

## Approval Rules

- `safe` actions may run immediately.
- `medium` actions should require approval for the MVP unless config changes that policy later.
- `dangerous` actions must always require human approval.
- Rejected actions must never execute.

## Persistence Requirements

Each step must be auditable: the model decision, chosen tools, validation result, approval state, and final outcome all belong in the timeline record.
