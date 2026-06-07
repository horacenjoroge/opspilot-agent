import pytest
from httpx import ASGITransport, AsyncClient

from app.schemas.incident import IncidentCreate
from app.schemas.approval import ApprovalRequestCreate
from app.schemas.enums import RiskLevel
from app.services.approvals import ApprovalService
from app.services.incidents import IncidentService


@pytest.mark.anyio
async def test_approval_endpoints_support_list_get_approve_and_reject(app_with_test_db, db_session) -> None:
    service = ApprovalService(db_session)
    incident_service = IncidentService(db_session)
    first_incident = incident_service.create_incident(
        IncidentCreate(
            title="Approval route incident one",
            description="Seed incident for approval route coverage.",
            source="test",
            severity="high",
        )
    )
    second_incident = incident_service.create_incident(
        IncidentCreate(
            title="Approval route incident two",
            description="Seed incident for approval rejection coverage.",
            source="test",
            severity="high",
        )
    )
    first = service.create_request(
        ApprovalRequestCreate(
            incident_id=first_incident.id,
            action_name="restart_api_workers_simulation",
            risk_level=RiskLevel.dangerous,
            reason="API workers are unhealthy.",
            expected_impact="Short restart impact.",
            rollback_plan="Restore previous worker version.",
            action_payload_json={
                "incident_id": first_incident.id,
                "action_name": "restart_api_workers_simulation",
                "scenario": "high_api_error_rate",
            },
        )
    )
    second = service.create_request(
        ApprovalRequestCreate(
            incident_id=second_incident.id,
            action_name="rollback_deployment_simulation",
            risk_level=RiskLevel.dangerous,
            reason="Latest deployment correlates with failures.",
            expected_impact="Traffic returns to prior build.",
            rollback_plan="Redeploy current build if rollback is worse.",
            action_payload_json={
                "incident_id": second_incident.id,
                "action_name": "rollback_deployment_simulation",
                "scenario": "high_api_error_rate",
            },
        )
    )

    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        list_response = await client.get("/api/approvals")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 2

        get_response = await client.get(f"/api/approvals/{first.id}")
        assert get_response.status_code == 200
        assert get_response.json()["action_name"] == "restart_api_workers_simulation"

        approve_response = await client.post(
            f"/api/approvals/{first.id}/approve",
            json={"approved_by": "oncall.engineer"},
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"

        reject_response = await client.post(
            f"/api/approvals/{second.id}/reject",
            json={"approved_by": "incident.commander"},
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["status"] == "rejected"

        not_found_response = await client.get("/api/approvals/999")
        assert not_found_response.status_code == 404
