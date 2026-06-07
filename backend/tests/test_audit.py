from app.schemas.incident import IncidentCreate
from app.services.audit import AuditService
from app.services.incidents import IncidentService


def test_incident_creation_is_audited(db_session) -> None:
    incident = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="Database latency spike",
            description="Latency increased above SLA.",
            source="datadog",
            severity="high",
        )
    )

    audit_logs = AuditService(db_session).list_for_target(
        target_type="incident",
        target_id=str(incident.id),
    )

    assert len(audit_logs) == 1
    assert audit_logs[0].action == "incident.created"
    assert audit_logs[0].metadata_json["severity"] == "high"


def test_tool_calls_and_remediation_actions_can_be_audited(db_session) -> None:
    audit_service = AuditService(db_session)

    audit_service.log(
        actor="agent",
        action="tool.called",
        target_type="incident",
        target_id="7",
        metadata_json={"tool_name": "logs_tool"},
    )
    audit_service.log(
        actor="agent",
        action="remediation.executed",
        target_type="incident",
        target_id="7",
        metadata_json={"action_name": "restart_api_workers_simulation"},
    )
    db_session.commit()

    audit_logs = audit_service.list_for_target(target_type="incident", target_id="7")

    assert [log.action for log in audit_logs] == ["tool.called", "remediation.executed"]
