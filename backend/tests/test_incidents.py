import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.schemas.incident import IncidentCreate


@pytest.mark.anyio
async def test_create_list_get_and_update_incident(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        create_response = await client.post(
            "/api/incidents",
            json={
                "title": "High API error rate",
                "description": "Alert fired for sustained 5xx errors.",
                "source": "alertmanager",
                "severity": "high",
            },
        )
        assert create_response.status_code == 201
        incident = create_response.json()
        assert incident["status"] == "new"

        list_response = await client.get("/api/incidents")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        get_response = await client.get(f"/api/incidents/{incident['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "High API error rate"

        update_response = await client.patch(
            f"/api/incidents/{incident['id']}/status",
            json={"status": "triaging"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "triaging"


@pytest.mark.anyio
async def test_create_incident_rejects_invalid_severity(app_with_test_db) -> None:
    async with AsyncClient(transport=ASGITransport(app=app_with_test_db), base_url="http://testserver") as client:
        response = await client.post(
            "/api/incidents",
            json={
                "title": "Invalid severity",
                "description": "Bad enum value",
                "source": "manual",
                "severity": "urgent",
            },
        )

    assert response.status_code == 422


def test_incident_schema_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        IncidentCreate(
            title="Bad status payload",
            description="This should fail validation.",
            source="manual",
            severity="high",
            status="done",
        )
