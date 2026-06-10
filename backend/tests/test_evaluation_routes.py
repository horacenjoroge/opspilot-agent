import pytest
from httpx import ASGITransport, AsyncClient

from app.models.evaluation import EvaluationCaseResult, EvaluationRun


@pytest.mark.anyio
async def test_evaluation_api_runs_all_cases(app_with_test_db, db_session) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.post("/api/evals/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 5
    assert payload["passed"] == 5
    assert payload["failed"] == 0
    assert len(payload["results"]) == 5

    run = db_session.query(EvaluationRun).order_by(EvaluationRun.id.desc()).first()
    assert run is not None
    assert run.provider == "mock"
    assert run.status == "completed"
    assert run.total_cases == 5
    assert run.passed_cases == 5
    assert run.failed_cases == 0
    assert run.completed_at is not None
    assert run.duration_ms is not None

    case_results = (
        db_session.query(EvaluationCaseResult)
        .filter(EvaluationCaseResult.evaluation_run_id == run.id)
        .all()
    )
    assert len(case_results) == 5


@pytest.mark.anyio
async def test_evaluation_api_runs_single_case(app_with_test_db, db_session) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.post("/api/evals/run/database_latency")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"] == "database_latency"
    assert payload["passed"] is True
    assert payload["actual_final_status"] == "resolved"

    run = db_session.query(EvaluationRun).order_by(EvaluationRun.id.desc()).first()
    assert run is not None
    assert run.total_cases == 1
    assert run.passed_cases == 1
    assert run.failed_cases == 0


@pytest.mark.anyio
async def test_evaluation_history_endpoint_returns_paginated_runs(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        first = await client.post("/api/evals/run/database_latency")
        second = await client.post("/api/evals/run/ambiguous_alert")
        history = await client.get("/api/evals/history", params={"limit": 1, "offset": 0})

    assert first.status_code == 200
    assert second.status_code == 200
    assert history.status_code == 200
    payload = history.json()
    assert payload["meta"]["limit"] == 1
    assert payload["meta"]["offset"] == 0
    assert payload["meta"]["total"] >= 2
    assert len(payload["items"]) == 1
    assert payload["items"][0]["provider"] == "mock"
