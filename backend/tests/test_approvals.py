from app.schemas.approval import ApprovalRequestCreate
from app.schemas.enums import ApprovalStatus, RiskLevel
from app.services.approvals import ApprovalService
from app.services.audit import AuditService
from app.services.incidents import IncidentService
from app.schemas.incident import IncidentCreate


def _create_incident(db_session, *, incident_id_seed_title: str):
    return IncidentService(db_session).create_incident(
        IncidentCreate(
            title=incident_id_seed_title,
            description="Seed incident for approval workflow tests.",
            source="test",
            severity="high",
        )
    )


def test_approval_request_can_be_created_and_approved(db_session) -> None:
    service = ApprovalService(db_session)
    incident = _create_incident(db_session, incident_id_seed_title="Approval target incident")

    approval_request = service.create_request(
        ApprovalRequestCreate(
            incident_id=incident.id,
            action_name="restart_api_workers_simulation",
            risk_level=RiskLevel.dangerous,
            reason="Workers are unhealthy.",
            expected_impact="Short worker disruption.",
            rollback_plan="Revert to previous worker image.",
            action_payload_json={
                "incident_id": incident.id,
                "action_name": "restart_api_workers_simulation",
                "scenario": "high_api_error_rate",
            },
        )
    )

    approved = service.approve_request(approval_request.id, "oncall.engineer")

    assert approved.status == ApprovalStatus.approved
    assert approved.approved_by == "oncall.engineer"

    audit_logs = AuditService(db_session).list_for_target(
        target_type="approval_request",
        target_id=str(approval_request.id),
    )
    assert [log.action for log in audit_logs] == ["approval.requested", "approval.approved"]

    incident_audit_logs = AuditService(db_session).list_for_target(target_type="incident", target_id=str(incident.id))
    assert "remediation.executed" in [log.action for log in incident_audit_logs]


def test_rejected_request_does_not_execute_action(db_session) -> None:
    service = ApprovalService(db_session)
    incident = _create_incident(db_session, incident_id_seed_title="Rejected approval target incident")

    approval_request = service.create_request(
        ApprovalRequestCreate(
            incident_id=incident.id,
            action_name="rollback_deployment_simulation",
            risk_level=RiskLevel.dangerous,
            reason="Latest deploy correlates with failures.",
            expected_impact="Rollback traffic to previous version.",
            rollback_plan="Redeploy current version if rollback worsens things.",
            action_payload_json={
                "incident_id": incident.id,
                "action_name": "rollback_deployment_simulation",
                "scenario": "high_api_error_rate",
            },
        )
    )

    rejected = service.reject_request(approval_request.id, "incident.commander")

    assert rejected.status == ApprovalStatus.rejected
    assert rejected.approved_by == "incident.commander"
    assert rejected.action_name == "rollback_deployment_simulation"

    incident_audit_logs = AuditService(db_session).list_for_target(target_type="incident", target_id=str(incident.id))
    assert [log.action for log in incident_audit_logs] == ["incident.created"]


def test_dangerous_action_policy_creates_approval_request(db_session) -> None:
    service = ApprovalService(db_session)
    incident = _create_incident(db_session, incident_id_seed_title="Policy approval target incident")

    approval_request = service.create_request_from_policy(
        incident_id=incident.id,
        action_name="restart_api_workers_simulation",
        reason="Workers are unhealthy.",
        expected_impact="Short interruption.",
        rollback_plan="Restore prior worker settings.",
        action_payload_json={
            "incident_id": incident.id,
            "action_name": "restart_api_workers_simulation",
            "scenario": "high_api_error_rate",
        },
    )

    assert approval_request.risk_level == RiskLevel.dangerous
    assert approval_request.status == ApprovalStatus.pending
