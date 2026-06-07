import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_dashboard_pages_render_without_postman(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        home = await client.get("/")
        demo = await client.get("/demo")
        incidents = await client.get("/incidents")
        approvals = await client.get("/approvals")

    assert home.status_code == 200
    assert "OpsPilot" in home.text
    assert demo.status_code == 200
    assert "Launch a scenario" in demo.text
    assert incidents.status_code == 200
    assert "Incident List" in incidents.text
    assert approvals.status_code == 200
    assert "Approval Queue" in approvals.text
