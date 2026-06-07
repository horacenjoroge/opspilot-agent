# Tool System

## Tool Registry Purpose

The registry is the backend control point for all agent capabilities. The model does not get arbitrary execution privileges. It can only recommend tool names that the backend has registered.

## Tool Interface

The shared tool interface includes:

- `name`
- `description`
- `risk_level`
- `input_schema`
- `execute(payload)`
- `run(validated_payload)`

## Tool Allowlist

Only registered tools may run. Unknown tool names are rejected before execution.

## Tool Input / Output Schema

Inputs:
- validated through Pydantic input schemas

Outputs:
- `ToolResult.status`
- `ToolResult.data`
- `ToolResult.summary`
- `ToolResult.error`

## Tool Risk Levels

- `safe`: read-only evidence collection and low-risk notifications
- `medium`: bounded changes that may still require approval
- `dangerous`: risky operational actions that require approval

## Existing Tools

### `logs_tool`
- returns seeded log evidence

### `metrics_tool`
- returns seeded operational metrics

### `health_tool`
- returns seeded health-check signals

### `deployment_tool`
- returns recent deployment context

### `runbook_tool`
- returns runbook guidance

### `remediation_tool`
- simulates backend-owned remediation actions

### `notification_tool`
- simulates low-risk outbound notifications

## How to Add a New Tool

1. create a tool class under `backend/app/tools`
2. define its input schema and risk level
3. implement `run`
4. register it in `ToolRegistry`
5. add tests
6. update docs

## How Tool Outputs Are Stored

Tool execution results are stored in `AgentStep` records and also contribute to the visible timeline. Some tool-related actions may also produce audit logs if they are operationally important.

## Tool Error Handling

- invalid input becomes a structured tool error
- execution errors become structured `ToolError`
- the agent stores failed tool steps rather than crashing blindly
