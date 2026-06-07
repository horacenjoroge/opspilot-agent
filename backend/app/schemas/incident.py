from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IncidentStatus, Severity


class IncidentBase(BaseModel):
    title: str = Field(..., examples=["API error spike in production"])
    description: str = Field(
        ...,
        examples=["Alertmanager detected a sustained 5xx rate above 12% for the public API."],
    )
    source: str = Field(..., examples=["alertmanager"])
    severity: Severity = Field(..., examples=["high"])


class IncidentCreate(IncidentBase):
    status: IncidentStatus = Field(default=IncidentStatus.new, examples=["new"])


class IncidentUpdateStatus(BaseModel):
    status: IncidentStatus = Field(..., examples=["triaging"])


class IncidentRead(IncidentBase):
    id: int = Field(..., examples=[1])
    status: IncidentStatus = Field(..., examples=["new"])
    root_cause_summary: str | None = Field(default=None, examples=["Database connections were exhausted."])
    recommended_action: str | None = Field(default=None, examples=["Restart API workers after approval."])
    final_report: str | None = Field(default=None, examples=["Incident mitigated and traffic stabilized."])
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
