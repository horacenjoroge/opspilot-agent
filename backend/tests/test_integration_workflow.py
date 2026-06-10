import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_full_workflow_create_run_approve_remediate_and_report(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        create_response = await client.post(
            "/api/demo/incidents/high_api_error_rate",
        )
        assert create_response.status_code == 201
        incident = create_response.json()

        run_response = await client.post(f"/api/incidents/{incident['id']}/run-agent")
        assert run_response.status_code == 200
        assert run_response.json()["status"] == "waiting_for_approval"

        approvals_response = await client.get("/api/approvals")
        assert approvals_response.status_code == 200
        approvals = approvals_response.json()
        assert len(approvals) == 1
        approval = approvals[0]
        assert approval["action_name"] == "restart_api_workers_simulation"
        assert approval["status"] == "pending"

        approve_response = await client.post(
            f"/api/approvals/{approval['id']}/approve",
            json={"approved_by": "integration.operator"},
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "approved"

        incident_detail = await client.get(f"/api/incidents/{incident['id']}")
        assert incident_detail.status_code == 200
        assert incident_detail.json()["status"] == "resolved"
        assert "Approved remediation" in incident_detail.json()["final_report"]

        timeline_response = await client.get(f"/api/incidents/{incident['id']}/timeline")
        assert timeline_response.status_code == 200
        timeline = timeline_response.json()
        labels = [item["label"] for item in timeline]
        categories = [item["category"] for item in timeline]
        assert "triage" in labels
        assert "logs_tool" in labels
        assert "remediation_recommendation" in labels
        assert "policy_decision" in labels
        assert "approval_request_created" in labels
        assert "approval_decision" in labels
        assert "approval_request" in categories
        assert "remediation.executed" in labels
        assert "final_report" in labels
        assert "memory.saved" in labels
        assert "memory_saved" in labels

        paginated_timeline_response = await client.get(
            f"/api/incidents/{incident['id']}/timeline",
            params={"limit": 2, "offset": 1, "include_meta": "true"},
        )
        assert paginated_timeline_response.status_code == 200
        paginated_timeline = paginated_timeline_response.json()
        assert paginated_timeline["meta"]["limit"] == 2
        assert paginated_timeline["meta"]["offset"] == 1
        assert paginated_timeline["meta"]["total"] >= len(timeline)
        assert len(paginated_timeline["items"]) == 2
