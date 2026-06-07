# Testing

## How to Run Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

## Test Types

### Unit Tests

Cover:
- schemas
- services
- policies
- registry behavior
- individual tools

### Integration Tests

Cover:
- incident API
- agent workflow
- approval flow
- dashboard rendering

### Agent Evaluation Tests

Cover deterministic scenarios:
- high API error rate
- queue backlog
- database latency spike
- ambiguous alert
- tool failure

### Failure Tests

Cover:
- tool failure
- unknown tool rejection
- max-step enforcement
- provider timeout fallback
- invalid model JSON fallback

### Security Tests

Cover:
- approval rejection blocks execution
- policy rejects unknown actions
- allowlist rejects unknown tools

## Current Coverage Status

Current suite status at the time of this update:
- `43 passed, 1 skipped`

The skipped test is the optional live Qwen smoke test without a configured key.

## Known Gaps

- no migration-tool tests because migrations are not implemented
- no production observability stack tests because Prometheus/Grafana/Sentry are future work
- no real infrastructure-action tests because remediation is simulated by design
