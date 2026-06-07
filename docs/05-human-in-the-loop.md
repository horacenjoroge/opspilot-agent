# Human In The Loop

## Backend Risk Policy Engine

OpsPilot uses a backend-owned risk policy engine. The model may recommend actions, but it cannot decide on its own what is allowed to execute.

Current status:

- Implemented: action risk map, unknown action rejection, approval gating for dangerous actions
- Implemented: explicit timeline storage of the risk-policy decision itself

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

## Approval-Required Actions

Examples of actions that should require approval:

- `restart_api_workers_simulation`
- `rollback_deployment_simulation`
- other dangerous or policy-defined medium-risk actions

Examples of actions that may run directly:

- `generate_report`
- `send_status_update`
- `create_issue`

## Model Cannot Override Approval

The approval gate is enforced in backend code, not prompt text. Even if the model requests a dangerous action, the backend still evaluates policy and blocks direct execution unless approval exists.

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

Current storage note:

- Implemented: approval requests, approval decisions, and approved remediation execution are persisted through `ApprovalRequest` and `AuditLog`
- Implemented: a first-class policy-decision timeline record is stored before the approval request is created

## Why This Matters

This design keeps OpsPilot aligned with the hackathon's Autopilot Agent theme while preserving backend-owned safety controls for real operational workflows.
