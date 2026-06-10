# API Reference

Swagger and schema links:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

OpsPilot exposes only the API routes that exist today. Dashboard HTML routes are intentionally not documented here because they are not part of the public JSON API.

## Cross-Cutting API Behavior

- all responses include `X-Request-ID`
- if the client sends `X-Request-ID`, OpsPilot reuses it
- validation and not-found failures return a shared `ErrorResponse`
- internal server errors return a sanitized `500` response without stack traces
- demo and evaluation APIs can be disabled at app startup with feature flags
- list endpoints support optional pagination and envelope metadata
- when `ENABLE_AUTH=true`, business routes require a valid session cookie or bearer token
- when `ENABLE_AUTH=false`, local demo mode bypasses auth safely

## Endpoint Table

| Method | Path | Purpose | Request Body | Response Body | Status Codes | Notes |
|---|---|---|---|---|---|---|
| `GET` | `/health` | Health check | none | `HealthResponse` | `200` | Shows configured LLM provider |
| `GET` | `/ready` | Readiness check | none | `ReadyResponse` | `200`, `503` | Checks DB connectivity and provider configuration |
| `POST` | `/api/auth/login` | Login and create a session | `LoginRequest` | `LoginResponse` | `200`, `400`, `401` | Sets the DB-backed session cookie |
| `POST` | `/api/auth/logout` | Logout current session | none | JSON status | `200`, `401` | Revokes cookie or bearer-token session |
| `GET` | `/api/auth/me` | Current auth status | none | `AuthStatusResponse` | `200`, `401` | Returns current signed-in user when auth is enabled |
| `POST` | `/api/incidents` | Create incident | `IncidentCreate` | `IncidentRead` | `201` | Manual incident creation |
| `GET` | `/api/incidents` | List incidents | none | `IncidentRead[]` | `200` | Newest first |
| `GET` | `/api/incidents/{incident_id}` | Get incident detail | none | `IncidentRead` | `200`, `404` | Includes diagnosis/report fields when available |
| `PATCH` | `/api/incidents/{incident_id}/status` | Update incident status | `IncidentUpdateStatus` | `IncidentRead` | `200`, `404` | Manual status change |
| `POST` | `/api/incidents/{incident_id}/run-agent` | Run the agent workflow | none | `AgentRunResponse` | `200`, `404` | Executes triage, tools, diagnosis, remediation logic |
| `GET` | `/api/incidents/{incident_id}/timeline` | Get merged timeline | none | `TimelineItem[]` | `200`, `404` | Includes agent steps, approvals, and audit logs |
| `GET` | `/api/approvals` | List approval requests | none | `ApprovalRequestRead[]` | `200` | Newest first |
| `GET` | `/api/approvals/{approval_id}` | Get approval request | none | `ApprovalRequestRead` | `200`, `404` | Single approval record |
| `POST` | `/api/approvals/{approval_id}/approve` | Approve risky action | `ApprovalDecision` | `ApprovalRequestRead` | `200`, `404` | Executes simulated remediation |
| `POST` | `/api/approvals/{approval_id}/reject` | Reject risky action | `ApprovalDecision` | `ApprovalRequestRead` | `200`, `404` | Blocks execution |
| `POST` | `/api/demo/incidents/{scenario_name}` | Seed demo incident | none | `IncidentRead` | `201`, `404` | Supported demo scenarios only |
| `POST` | `/api/evals/run` | Run all evaluation scenarios | none | `EvaluationRunSummary` | `200` | Mock-backed deterministic judge view |
| `POST` | `/api/evals/run/{scenario_name}` | Run one evaluation scenario | none | `EvaluationCaseResult` | `200`, `404` | Useful for demos and debugging |
| `GET` | `/api/evals/history` | List persisted evaluation runs | none | `EvaluationHistoryResponse` | `200` | Returns latest stored eval runs with pagination metadata |

## Main Example Payloads

### `GET /ready`

Healthy response:

```json
{
  "status": "ready",
  "service": "opspilot",
  "llm_provider": "mock",
  "timestamp": "2026-06-08T10:20:00Z",
  "checks": {
    "database": {
      "ok": true,
      "detail": "Database connection succeeded."
    },
    "provider": {
      "ok": true,
      "detail": "Mock provider is configured for local/demo readiness."
    }
  }
}
```

Unhealthy Qwen configuration response:

```json
{
  "status": "not_ready",
  "service": "opspilot",
  "llm_provider": "qwen",
  "timestamp": "2026-06-08T10:21:00Z",
  "checks": {
    "database": {
      "ok": true,
      "detail": "Database connection succeeded."
    },
    "provider": {
      "ok": false,
      "detail": "Missing required Qwen configuration: QWEN_API_KEY, QWEN_BASE_URL."
    }
  }
}
```

### `POST /api/incidents`

Request:

```json
{
  "title": "API error spike in production",
  "description": "Alertmanager detected a sustained 5xx rate above 12% for the public API.",
  "source": "alertmanager",
  "severity": "high",
  "status": "new"
}
```

Response:

```json
{
  "id": 1,
  "title": "API error spike in production",
  "description": "Alertmanager detected a sustained 5xx rate above 12% for the public API.",
  "source": "alertmanager",
  "severity": "high",
  "status": "new",
  "root_cause_summary": null,
  "recommended_action": null,
  "final_report": null,
  "created_at": "2026-06-07T10:15:00Z",
  "updated_at": "2026-06-07T10:15:00Z"
}
```

### `POST /api/incidents/{incident_id}/run-agent`

Response:

```json
{
  "incident_id": 1,
  "status": "waiting_for_approval",
  "recommended_action": "Restart API workers after validating the database pool is stable.",
  "error": null
}
```

Fallback example when the provider is unavailable:

```json
{
  "incident_id": 7,
  "status": "resolved",
  "recommended_action": "Generate a structured incident report and hand off for manual review.",
  "error": null
}
```

### `GET /api/incidents/{incident_id}/timeline`

Response excerpt:

```json
[
  {
    "occurred_at": "2026-06-07T10:15:12Z",
    "category": "agent_step",
    "label": "triage",
    "status": "success",
    "details": {
      "step_number": 1,
      "tool_name": null,
      "model_summary": "Elevated API errors require logs, metrics, health, deployment, and runbook evidence.",
      "input_json": null,
      "output_json": {
        "severity": "high",
        "incident_type": "high_api_error_rate",
        "recommended_tools": ["logs_tool", "metrics_tool", "health_tool", "deployment_tool", "runbook_tool"],
        "reasoning_summary": "Elevated API errors require logs, metrics, health, deployment, and runbook evidence.",
        "requires_human_approval": false
      }
    }
  }
]
```

### `POST /api/approvals/{approval_id}/approve`

Request:

```json
{
  "approved_by": "oncall.engineer"
}
```

Response:

```json
{
  "id": 1,
  "incident_id": 1,
  "action_name": "restart_api_workers_simulation",
  "risk_level": "dangerous",
  "reason": "Restarting workers may clear exhausted DB connections but affects live traffic.",
  "expected_impact": "Short-lived request disruption while workers recycle.",
  "rollback_plan": "Cancel restart and revert to previous worker deployment settings if errors worsen.",
  "action_payload_json": {
    "incident_id": 1,
    "action_name": "restart_api_workers_simulation",
    "scenario": "high_api_error_rate"
  },
  "status": "approved",
  "requested_at": "2026-06-07T10:16:00Z",
  "approved_by": "oncall.engineer",
  "approved_at": "2026-06-07T10:17:00Z"
}
```

### `POST /api/evals/run`

Response excerpt:

```json
{
  "total": 5,
  "passed": 5,
  "failed": 0,
  "results": [
    {
      "scenario": "high_api_error_rate",
      "passed": true,
      "incident_id": 14,
      "actual_severity": "high",
      "actual_tools": ["logs_tool", "metrics_tool", "health_tool", "deployment_tool", "runbook_tool"],
      "actual_requires_approval": true,
      "actual_final_status": "waiting_for_approval",
      "diagnosis_text": "The API error spike is consistent with database connection exhaustion in the application pool.",
      "checks": {
        "severity": true,
        "tools": true,
        "approval": true,
        "final_status": true,
        "diagnosis_keywords": true
      },
      "expected": {
        "scenario": "high_api_error_rate",
        "expected_severity": "high",
        "expected_tools": ["logs_tool", "metrics_tool", "health_tool", "deployment_tool", "runbook_tool"],
        "expected_requires_approval": true,
        "expected_final_status": "waiting_for_approval",
        "expected_diagnosis_keywords": ["database", "connection", "exhaustion"]
      }
    }
  ]
}
```

## Common Error Shape

Example:

```json
{
  "detail": "Incident 999 was not found.",
  "error_code": "http_404",
  "request_id": "judge-request-123",
  "errors": []
}
```

## Feature Flags

- `ENABLE_DEMO_ROUTES=false` removes `/api/demo/*`
- `ENABLE_EVAL_ROUTES=false` removes `/api/evals/*`
- `ENABLE_DASHBOARD=false` removes the HTML dashboard routes

## Auth Notes

- `admin`: full access
- `operator`: create incidents, update status, run agent, launch demo incidents, run evals
- `reviewer`: read-only on incidents plus approval/reject permissions
- `viewer`: read-only access
- dashboard login is only enforced when both `ENABLE_AUTH=true` and `ENABLE_DASHBOARD_AUTH=true`

## Pagination And Filtering

- `GET /api/incidents`
  - filters: `status`, `severity`
  - pagination: `limit`, `offset`
- `GET /api/approvals`
  - pagination: `limit`, `offset`
- `GET /api/incidents/{incident_id}/timeline`
  - pagination: `limit`, `offset`
- add `include_meta=true` to any of the list endpoints above to receive:

```json
{
  "items": [],
  "meta": {
    "total": 25,
    "limit": 10,
    "offset": 0
  }
}
```

## Future Work

Planned but not implemented as API endpoints:

- dedicated live Qwen smoke-test endpoint
- public incident memory search endpoint
- deployment/admin control endpoints
- webhook-based real alert ingestion endpoint
