# Monitoring Setup

## Implemented Today

- health endpoint: `/health`
- app logs: standard application/runtime logs
- agent timeline: persisted incident timeline via `AgentStep`
- audit logs: persisted operational records via `AuditLog`
- error handling: structured failures and safe fallbacks

## Request IDs

Not implemented today.

## Metrics

No Prometheus metrics endpoint is implemented today.

## Future Work

- Prometheus
- Grafana
- Sentry
- alert webhooks
- request IDs and correlation IDs
