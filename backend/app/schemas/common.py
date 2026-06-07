from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Incident 999 was not found."])


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["opspilot"])
    llm_provider: str = Field(..., examples=["mock"])


class AgentRunResponse(BaseModel):
    incident_id: int = Field(..., examples=[12])
    status: str = Field(..., examples=["waiting_for_approval"])
    recommended_action: str | None = Field(
        default=None,
        examples=["Restart API workers after validating the database pool is stable."],
    )
    error: str | None = Field(
        default=None,
        examples=["Agent exceeded max_steps=1."],
    )
