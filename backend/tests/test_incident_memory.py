import pytest

from app.agents.incident_agent import IncidentAgent
from app.schemas.incident import IncidentCreate
from app.services.incident_memory import IncidentMemoryService
from app.services.incidents import IncidentService


@pytest.mark.anyio
async def test_resolved_incident_saves_memory(db_session) -> None:
    incident = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="Database latency spike affecting checkout",
            description="Database latency increased sharply and is propagating to API response times.",
            source="demo:database_latency",
            severity="high",
        )
    )

    result = await IncidentAgent(db_session).run(incident.id)

    assert result["status"] == "resolved"

    memories = IncidentMemoryService(db_session).find_similar(
        incident_type="database_latency",
        symptoms="Database latency increased sharply and is propagating to API response times.",
    )
    assert len(memories) == 1
    assert memories[0].memory.incident_id == incident.id
    assert memories[0].memory.successful_fix == "generate_report"


@pytest.mark.anyio
async def test_agent_retrieves_similar_memory_before_diagnosis(db_session) -> None:
    first = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="Database latency spike affecting checkout",
            description="Database latency increased sharply and is propagating to API response times.",
            source="demo:database_latency",
            severity="high",
        )
    )
    await IncidentAgent(db_session).run(first.id)

    second = IncidentService(db_session).create_incident(
        IncidentCreate(
            title="Recurring database latency spike",
            description="Database latency increased sharply again and checkout traffic is slowing down.",
            source="demo:database_latency",
            severity="high",
        )
    )
    await IncidentAgent(db_session).run(second.id)

    used_memories = IncidentMemoryService(db_session).list_used_for_incident(second.id)
    assert len(used_memories) == 1
    assert used_memories[0].incident_id == first.id

