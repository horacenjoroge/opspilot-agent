# Human In The Loop

## Risk Model

OpsPilot separates recommended actions by risk:

- `safe`: can execute immediately
- `medium`: should require approval in the MVP unless policy is explicitly relaxed
- `dangerous`: always requires human approval

## Approval Flow

1. The model recommends an action in strict JSON.
2. The backend maps that action to a known tool and risk level.
3. If the action is risky, the backend creates an approval request instead of executing it.
4. The approval request includes the reason, expected impact, risk summary, and rollback plan.
5. A human approves or rejects the action through the approvals API or dashboard.

## Rejection Behavior

- Rejected actions must not execute.
- The incident timeline must record who rejected the request and when.
- The workflow can continue with alternative safe actions or stop with a documented outcome.

## Audit Requirements

Every approval event must be persisted, including:

- proposed action
- risk level
- decision outcome
- approver identity
- timestamps
- remediation execution result if approved

## Why This Matters

This design keeps OpsPilot aligned with the hackathon's Autopilot Agent theme while preserving backend-owned safety controls for real operational workflows.
