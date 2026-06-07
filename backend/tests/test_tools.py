import pytest

from app.services.audit import AuditService
from app.tools.registry import ToolNotFoundError, ToolRegistry


@pytest.mark.anyio
async def test_registry_lists_known_tools_and_rejects_unknown_tools(db_session) -> None:
    registry = ToolRegistry(audit_service=AuditService(db_session))

    assert registry.list_tools() == [
        "deployment_tool",
        "health_tool",
        "logs_tool",
        "metrics_tool",
        "notification_tool",
        "remediation_tool",
        "runbook_tool",
    ]

    with pytest.raises(ToolNotFoundError):
        registry.get_tool("shell_exec_tool")


@pytest.mark.anyio
async def test_high_api_error_scenario_returns_db_connection_exhaustion_evidence(db_session) -> None:
    registry = ToolRegistry(audit_service=AuditService(db_session))

    logs_result = await registry.execute(
        "logs_tool",
        {"scenario": "high_api_error_rate", "query": "connection"},
    )
    metrics_result = await registry.execute(
        "metrics_tool",
        {"scenario": "high_api_error_rate", "metric_names": ["db_connections", "error_rate"]},
    )

    assert logs_result.status.value == "success"
    assert "too many clients already" in " ".join(logs_result.data["logs"]).lower()
    assert metrics_result.data["metrics"]["db_connections"] == 120


@pytest.mark.anyio
async def test_queue_backlog_and_database_latency_scenarios_return_expected_evidence(db_session) -> None:
    registry = ToolRegistry(audit_service=AuditService(db_session))

    queue_metrics = await registry.execute("metrics_tool", {"scenario": "queue_backlog"})
    queue_health = await registry.execute("health_tool", {"scenario": "queue_backlog"})
    db_metrics = await registry.execute("metrics_tool", {"scenario": "database_latency"})
    db_runbook = await registry.execute("runbook_tool", {"scenario": "database_latency"})

    assert queue_metrics.data["metrics"]["queue_depth"] == 12540
    assert queue_health.data["health"]["worker"] == "degraded"
    assert db_metrics.data["metrics"]["latency_p95_ms"] == 2240
    assert "slow query" in db_runbook.data["runbook"].lower()


@pytest.mark.anyio
async def test_tool_failure_scenario_returns_structured_failure(db_session) -> None:
    registry = ToolRegistry(audit_service=AuditService(db_session))

    result = await registry.execute("logs_tool", {"scenario": "tool_failure", "query": "errors"})

    assert result.status.value == "failed"
    assert result.error is not None
    assert result.error.code == "tool_unavailable"


@pytest.mark.anyio
async def test_safe_and_dangerous_actions_behave_correctly_and_create_audit_logs(db_session) -> None:
    audit_service = AuditService(db_session)
    registry = ToolRegistry(audit_service=audit_service)

    safe_result = await registry.execute(
        "remediation_tool",
        {
            "incident_id": 1,
            "action_name": "generate_report",
            "scenario": "database_latency",
            "actor": "agent",
        },
    )
    blocked_result = await registry.execute(
        "remediation_tool",
        {
            "incident_id": 1,
            "action_name": "restart_api_workers_simulation",
            "scenario": "high_api_error_rate",
            "actor": "agent",
        },
    )
    approved_result = await registry.execute(
        "remediation_tool",
        {
            "incident_id": 1,
            "action_name": "restart_api_workers_simulation",
            "scenario": "high_api_error_rate",
            "actor": "incident.commander",
            "approved": True,
        },
    )
    notification_result = await registry.execute(
        "notification_tool",
        {
            "incident_id": 1,
            "action_name": "send_status_update",
            "channel": "slack",
            "message": "Investigating API error spike.",
            "actor": "incident.commander",
        },
    )

    assert safe_result.status.value == "success"
    assert blocked_result.status.value == "failed"
    assert blocked_result.error is not None
    assert blocked_result.error.code == "approval_required"
    assert approved_result.status.value == "success"
    assert notification_result.status.value == "success"

    audit_logs = audit_service.list_for_target(target_type="incident", target_id="1")
    assert [log.action for log in audit_logs] == [
        "remediation.executed",
        "remediation.blocked",
        "remediation.executed",
        "notification.sent",
    ]
