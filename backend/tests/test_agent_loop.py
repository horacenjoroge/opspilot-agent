import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.incident_agent import IncidentAgent
from app.llm.base import LLMProvider
from app.schemas.incident import IncidentCreate
from app.services.incidents import IncidentService


class UnknownToolProvider:
    async def generate_json(self, *, system: str, user: str, schema_name: str) -> dict:
        if schema_name == "triage":
            return {
                "severity": "high",
                "incident_type": "high_api_error_rate",
                "recommended_tools": ["shell_exec_tool"],
                "reasoning_summary": "Use an unapproved tool.",
                "requires_human_approval": False,
            }
        return {}


@pytest.mark.anyio
async def test_agent_happy_path_creates_approval_request_and_timeline(app_with_test_db, db_session) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        demo_response = await client.post("/api/demo/incidents/high_api_error_rate")
        assert demo_response.status_code == 201
        incident = demo_response.json()

        run_response = await client.post(f"/api/incidents/{incident['id']}/run-agent")
        assert run_response.status_code == 200
        assert run_response.json()["status"] == "waiting_for_approval"

        timeline_response = await client.get(f"/api/incidents/{incident['id']}/timeline")
        assert timeline_response.status_code == 200
        categories = [item["category"] for item in timeline_response.json()]
        assert "agent_step" in categories
        assert "approval_request" in categories


@pytest.mark.anyio
async def test_agent_handles_tool_failure_without_crashing(db_session) -> None:
    incident = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="Investigation dependency failure during alert",
            description="A tool failure occurred during investigation.",
            source="demo:tool_failure",
            severity="medium",
        )
    )

    result = await IncidentAgent(db_session).run(incident.id)

    assert result["status"] in {"waiting_for_approval", "resolved"}


@pytest.mark.anyio
async def test_agent_rejects_unknown_tool_and_fails_safely(db_session) -> None:
    incident = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="Unknown tool test",
            description="Alert with provider returning an unknown tool.",
            source="manual",
            severity="high",
        )
    )

    result = await IncidentAgent(db_session, provider=UnknownToolProvider()).run(incident.id)

    assert result["status"] == "failed"
    assert "Unknown tools recommended by model" in result["error"]


@pytest.mark.anyio
async def test_agent_enforces_max_step_limit(db_session) -> None:
    incident = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="High API error rate in production",
            description="Alertmanager detected sustained 5xx errors.",
            source="demo:high_api_error_rate",
            severity="high",
        )
    )

    result = await IncidentAgent(db_session, max_steps=1).run(incident.id)

    assert result["status"] == "failed"
    assert "max_steps" in result["error"]
