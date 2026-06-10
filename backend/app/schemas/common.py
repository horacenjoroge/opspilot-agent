from datetime import datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Incident 999 was not found."])
    error_code: str = Field(..., examples=["http_404"])
    request_id: str = Field(..., examples=["7f02c6a5-9126-4f0e-846e-2792cce7ab80"])
    errors: list[dict] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["opspilot"])
    llm_provider: str = Field(..., examples=["mock"])


class ReadinessCheck(BaseModel):
    ok: bool = Field(..., examples=[True])
    detail: str = Field(..., examples=["Database connection succeeded."])


class ReadyResponse(BaseModel):
    status: str = Field(..., examples=["ready"])
    service: str = Field(..., examples=["opspilot"])
    llm_provider: str = Field(..., examples=["mock"])
    timestamp: datetime
    checks: dict[str, ReadinessCheck] = Field(default_factory=dict)


class PaginationMeta(BaseModel):
    total: int = Field(..., examples=[25])
    limit: int = Field(..., examples=[10])
    offset: int = Field(..., examples=[0])


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
