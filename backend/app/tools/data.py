SCENARIO_DATA = {
    "high_api_error_rate": {
        "logs": [
            "ERROR api: database connection pool exhausted after 120 active sessions",
            "ERROR api: psycopg connection refused due to too many clients already",
            "WARN api: request latency degraded after connection retry storm",
        ],
        "metrics": {
            "error_rate": "12.4%",
            "latency_p95_ms": 1840,
            "db_connections": 120,
            "queue_depth": 24,
        },
        "health": {
            "api": "degraded",
            "database": "degraded",
            "worker": "healthy",
        },
        "deployment": {
            "version": "api-2026.06.07.1",
            "deployed_at": "2026-06-07T07:40:00Z",
            "changed_files": ["app/db/pool.py", "app/api/orders.py"],
        },
        "runbook": "# API Error Rate Runbook\n1. Confirm DB pool saturation.\n2. Review recent deploys.\n3. Consider restarting API workers with approval.",
    },
    "queue_backlog": {
        "logs": [
            "WARN worker: queue backlog exceeded threshold for 15 minutes",
            "WARN worker: job retry count increasing for image-processing queue",
        ],
        "metrics": {
            "error_rate": "1.1%",
            "latency_p95_ms": 430,
            "db_connections": 48,
            "queue_depth": 12540,
        },
        "health": {
            "api": "healthy",
            "database": "healthy",
            "worker": "degraded",
        },
        "deployment": {
            "version": "worker-2026.06.07.2",
            "deployed_at": "2026-06-07T05:10:00Z",
            "changed_files": ["app/workers/consumer.py", "app/queue/retry.py"],
        },
        "runbook": "# Queue Backlog Runbook\n1. Check worker saturation.\n2. Evaluate scaling workers.\n3. Review retry storm conditions.",
    },
    "database_latency": {
        "logs": [
            "WARN database: slow query threshold exceeded for SELECT orders_summary",
            "WARN api: upstream database latency propagated to checkout endpoints",
        ],
        "metrics": {
            "error_rate": "2.3%",
            "latency_p95_ms": 2240,
            "db_connections": 92,
            "queue_depth": 310,
        },
        "health": {
            "api": "degraded",
            "database": "degraded",
            "worker": "healthy",
        },
        "deployment": {
            "version": "api-2026.06.06.9",
            "deployed_at": "2026-06-06T23:15:00Z",
            "changed_files": ["app/reporting/queries.sql", "app/db/indexes.py"],
        },
        "runbook": "# Database Latency Runbook\n1. Inspect slow query metrics.\n2. Capture evidence.\n3. Escalate to DBA if changes are risky.",
    },
    "ambiguous_alert": {
        "logs": [
            "INFO monitoring: alert signal is weak and spans multiple services",
        ],
        "metrics": {
            "error_rate": "0.8%",
            "latency_p95_ms": 510,
            "db_connections": 52,
            "queue_depth": 220,
        },
        "health": {
            "api": "healthy",
            "database": "healthy",
            "worker": "healthy",
        },
        "deployment": {
            "version": "platform-2026.06.07.0",
            "deployed_at": "2026-06-07T00:20:00Z",
            "changed_files": ["infra/alerts.yaml"],
        },
        "runbook": "# Ambiguous Alert Runbook\n1. Gather broad read-only evidence.\n2. Avoid risky actions until a clearer diagnosis exists.",
    },
    "tool_failure": {
        "logs": [
            "ERROR observability: log index unavailable for the requested window",
        ],
        "metrics": {
            "error_rate": "4.2%",
            "latency_p95_ms": 980,
            "db_connections": 61,
            "queue_depth": 640,
        },
        "health": {
            "api": "degraded",
            "database": "healthy",
            "worker": "healthy",
        },
        "deployment": {
            "version": "api-2026.06.07.3",
            "deployed_at": "2026-06-07T08:05:00Z",
            "changed_files": ["app/observability/logging.py"],
        },
        "runbook": "# Tool Failure Runbook\n1. Record the failed dependency.\n2. Use fallback evidence paths.\n3. Avoid overconfident remediation.",
    },
}


def get_scenario_data(scenario: str) -> dict:
    if scenario not in SCENARIO_DATA:
        raise KeyError(f"Unknown scenario: {scenario}")
    return SCENARIO_DATA[scenario]
