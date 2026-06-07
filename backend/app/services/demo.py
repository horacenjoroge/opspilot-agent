from app.schemas.incident import IncidentCreate
from app.schemas.enums import Severity
from app.services.incidents import IncidentService


DEMO_INCIDENTS = {
    "high_api_error_rate": IncidentCreate(
        title="High API error rate in production",
        description="Alertmanager detected sustained 5xx errors and signs of database connection exhaustion in the public API.",
        source="demo:high_api_error_rate",
        severity=Severity.high,
    ),
    "queue_backlog": IncidentCreate(
        title="Queue backlog is growing rapidly",
        description="The background job queue depth is rising while worker throughput is falling behind.",
        source="demo:queue_backlog",
        severity=Severity.high,
    ),
    "database_latency": IncidentCreate(
        title="Database latency spike affecting checkout",
        description="Database latency increased sharply and is propagating to API response times.",
        source="demo:database_latency",
        severity=Severity.high,
    ),
    "ambiguous_alert": IncidentCreate(
        title="Ambiguous platform alert",
        description="An ambiguous alert fired with weak evidence across multiple services.",
        source="demo:ambiguous_alert",
        severity=Severity.medium,
    ),
    "tool_failure": IncidentCreate(
        title="Investigation dependency failure during alert",
        description="A production alert fired while the log index for the incident window is unavailable.",
        source="demo:tool_failure",
        severity=Severity.medium,
    ),
}


class DemoScenarioNotFoundError(ValueError):
    pass


class DemoService:
    def __init__(self, incident_service: IncidentService) -> None:
        self.incident_service = incident_service

    def create_demo_incident(self, scenario_name: str):
        payload = DEMO_INCIDENTS.get(scenario_name)
        if payload is None:
            raise DemoScenarioNotFoundError(f"Unknown demo scenario '{scenario_name}'.")
        return self.incident_service.create_incident(payload)
