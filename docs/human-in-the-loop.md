# Human In The Loop

## Why Human Approval Exists

OpsPilot is designed to accelerate incident response, not to grant unrestricted LLM control over production changes. Human approval exists to keep risky remediation under operator control.

## Risk Levels

- `safe`
- `medium`
- `dangerous`

## Which Actions Can Execute Immediately

Examples:
- `generate_report`
- `send_status_update`
- `create_issue`

## Which Actions Require Approval

Implemented examples:
- `restart_api_workers_simulation`
- `rollback_deployment_simulation`
- medium-risk actions when the current configuration requires approval

## Approval Request Fields

- `incident_id`
- `action_name`
- `risk_level`
- `reason`
- `expected_impact`
- `rollback_plan`
- `action_payload_json`
- `requested_at`
- `approved_by`
- `approved_at`

## Approve Flow

1. agent recommends remediation
2. backend risk policy classifies the action
3. approval request is created
4. operator approves
5. simulated remediation executes
6. final report and memory are saved

## Reject Flow

1. agent recommends remediation
2. backend creates approval request
3. operator rejects
4. execution does not occur
5. decision remains auditable

## Audit Logging

Approval requests and decisions are stored in:

- `ApprovalRequest`
- `AuditLog`
- explicit `AgentStep` records

## Safety Guarantees

- the model cannot override approval policy
- unknown actions are rejected
- dangerous actions do not execute without approval
- remediation remains simulated in the current implementation

## Demo Explanation

The main demo scenario should show a dangerous action that pauses for approval so judges can clearly see that OpsPilot is not a blind autonomous bot.
