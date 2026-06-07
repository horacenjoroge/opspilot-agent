from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.models.agent_step import AgentStep
from app.schemas.agent_step import AgentStepCreate


SENSITIVE_KEYS = {"authorization", "token", "api_key", "secret", "password"}


def _redact_sensitive(value: object) -> object:
    if isinstance(value, Mapping):
        redacted: dict[str, object] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                redacted[key] = "***redacted***"
            else:
                redacted[key] = _redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive(item) for item in value]
    return value


class AgentStepService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_step(self, payload: AgentStepCreate) -> AgentStep:
        data = payload.model_dump()
        data["input_json"] = _redact_sensitive(payload.input_json)
        data["output_json"] = _redact_sensitive(payload.output_json)
        step = AgentStep(**data)
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def list_for_incident(self, incident_id: int) -> list[AgentStep]:
        return (
            self.db.query(AgentStep)
            .filter(AgentStep.incident_id == incident_id)
            .order_by(AgentStep.step_number.asc(), AgentStep.id.asc())
            .all()
        )

    def next_step_number(self, incident_id: int) -> int:
        return len(self.list_for_incident(incident_id)) + 1
