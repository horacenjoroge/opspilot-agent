import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_dashboard_pages_render_without_postman(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        home = await client.get("/")
        architecture = await client.get("/architecture")
        demo = await client.get("/demo")
        incidents = await client.get("/incidents")
        approvals = await client.get("/approvals")
        evals = await client.get("/evals")

    assert home.status_code == 200
    assert "OpsPilot" in home.text
    assert "How To Use OpsPilot" in home.text
    assert architecture.status_code == 200
    assert "Why OpsPilot is an agent, not a chatbot" in architecture.text
    assert demo.status_code == 200
    assert "Launch a scenario" in demo.text
    assert incidents.status_code == 200
    assert "Incident List" in incidents.text
    assert approvals.status_code == 200
    assert "Approval Queue" in approvals.text
    assert evals.status_code == 200
    assert "Scenario Runner" in evals.text


@pytest.mark.anyio
async def test_incident_detail_shows_memory_panel(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        first = await client.post("/api/demo/incidents/database_latency")
        assert first.status_code == 201
        await client.post(f"/api/incidents/{first.json()['id']}/run-agent")

        second = await client.post("/api/demo/incidents/database_latency")
        assert second.status_code == 201
        await client.post(f"/api/incidents/{second.json()['id']}/run-agent")

        detail = await client.get(f"/incidents/{second.json()['id']}")

    assert detail.status_code == 200
    assert "Similar Incident Memory" in detail.text
    assert "generate_report" in detail.text
    assert "Policy Decision" in detail.text
    assert "Timeline" in detail.text
