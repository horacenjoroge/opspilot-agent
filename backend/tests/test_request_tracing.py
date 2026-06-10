import logging

import pytest
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient


@pytest.mark.anyio
async def test_request_id_is_reused_when_provided(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.get("/health", headers={"X-Request-ID": "judge-request-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "judge-request-123"


@pytest.mark.anyio
async def test_request_id_is_generated_when_missing(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


@pytest.mark.anyio
async def test_not_found_returns_structured_error_with_request_id(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.get("/api/incidents/999", headers={"X-Request-ID": "missing-incident-1"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "missing-incident-1"
    assert response.json() == {
        "detail": "Incident 999 was not found.",
        "error_code": "http_404",
        "request_id": "missing-incident-1",
        "errors": [],
    }


@pytest.mark.anyio
async def test_validation_error_returns_structured_error_with_request_id(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.post(
            "/api/incidents",
            headers={"X-Request-ID": "validation-1"},
            json={
                "title": "Invalid severity",
                "description": "Bad enum value",
                "source": "manual",
                "severity": "urgent",
            },
        )

    payload = response.json()
    assert response.status_code == 422
    assert response.headers["X-Request-ID"] == "validation-1"
    assert payload["detail"] == "Request validation failed."
    assert payload["error_code"] == "validation_error"
    assert payload["request_id"] == "validation-1"
    assert payload["errors"]


@pytest.mark.anyio
async def test_unhandled_exception_is_sanitized_and_logged(app_with_test_db, caplog) -> None:
    router = APIRouter()

    @router.get("/_test/runtime-error")
    async def runtime_error() -> dict:
        raise RuntimeError("secret internal failure")

    app_with_test_db.include_router(router)
    added_route_count = len(router.routes)
    caplog.set_level(logging.INFO, logger="opspilot.api")

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app_with_test_db, raise_app_exceptions=False),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/_test/runtime-error", headers={"X-Request-ID": "runtime-500"})
    finally:
        del app_with_test_db.router.routes[-added_route_count:]

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "runtime-500"
    assert response.json() == {
        "detail": "Internal server error.",
        "error_code": "internal_server_error",
        "request_id": "runtime-500",
        "errors": [],
    }
    assert "secret internal failure" not in response.text
    assert "request_id=runtime-500" in caplog.text
