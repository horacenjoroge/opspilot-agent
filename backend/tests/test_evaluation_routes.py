import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_evaluation_api_runs_all_cases(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.post("/api/evals/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert payload["passed"] == 5
    assert payload["failed"] == 0
    assert len(payload["results"]) == 5


@pytest.mark.anyio
async def test_evaluation_api_runs_single_case(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.post("/api/evals/run/database_latency")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"] == "database_latency"
    assert payload["passed"] is True
    assert payload["actual_final_status"] == "resolved"
