# Tool System

## Design Goal

Tools are the agent's only way to inspect evidence or propose actions. They provide constrained backend capabilities with explicit schemas, risk labels, and structured results.

## Tool Catalog

| Tool | Purpose |
|---|---|
| `logs_tool` | Read seeded logs and return relevant errors |
| `metrics_tool` | Return seeded metrics such as error rate, latency, DB connections, and queue depth |
| `health_tool` | Return service health states |
| `deployment_tool` | Return recent deployments and changed files |
| `runbook_tool` | Retrieve markdown runbook guidance |
| `remediation_tool` | Execute or simulate approved actions |
| `notification_tool` | Simulate Slack, email, or status-page updates |

## Shared Interface

```txt
name: string
description: string
input_schema: Pydantic model
risk_level: safe | medium | dangerous
run(input) -> ToolResult
```

## Tool Result Contract

```json
{
  "status": "success",
  "data": {},
  "summary": "",
  "error": null
}
```

## Input and Output Expectations

- Every tool receives validated input through a Pydantic schema.
- Every tool returns a serializable `ToolResult`.
- Failures should return structured errors instead of throwing raw infrastructure details into the agent loop.

## Tool Allowlist

The registry is the backend control point for tool safety.

- only registered tools may execute
- unknown tool names are rejected before execution
- the model does not get arbitrary code execution
- route handlers never call tools directly without going through the registry

Current status:

- Implemented: base tool interface, registry, allowlisted tools, unknown-tool rejection

## Tool Risk Levels

Each tool or action carries a backend-owned risk classification:

- `safe`: read-only evidence gathering and low-risk notifications
- `medium`: bounded operational changes that may still require approval
- `dangerous`: actions that can affect live traffic and always require approval

The model can recommend actions, but it cannot assign or override their risk.

## Risk Levels

- `safe`: read-only tools and low-risk notifications
- `medium`: actions that may change system behavior but are still bounded
- `dangerous`: actions like worker restarts or rollback simulations that require explicit approval

## Unknown Tools

If Qwen recommends a tool that is not registered, the backend must reject it, persist the rejection, and continue safely rather than improvising a new capability.

## Tool Error Handling

Tool execution is standardized:

- input payloads are validated before `run`
- expected failures return structured `ToolError`
- the agent stores the failed result instead of crashing
- remediation actions that require approval return an explicit approval-needed error until approved

## Evidence Storage In AgentStep

Tool evidence is stored as part of the incident timeline:

- `step_number`
- `type`
- `tool_name`
- `input_json`
- `output_json`
- `model_summary`
- `status`

Current honesty note:

- Implemented: tool outputs and failures are persisted in `AgentStep`
- To Implement: richer step fields such as `title`, normalized `summary`, and raw `model_json` for every model decision
