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

## Risk Levels

- `safe`: read-only tools and low-risk notifications
- `medium`: actions that may change system behavior but are still bounded
- `dangerous`: actions like worker restarts or rollback simulations that require explicit approval

## Unknown Tools

If Qwen recommends a tool that is not registered, the backend must reject it, persist the rejection, and continue safely rather than improvising a new capability.
