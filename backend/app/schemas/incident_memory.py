from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentMemoryRead(BaseModel):
    id: int = Field(..., examples=[1])
    incident_id: int = Field(..., examples=[4])
    incident_type: str = Field(..., examples=["high_api_error_rate"])
    symptoms: str = Field(..., examples=["5xx spike with database connection exhaustion signs."])
    tools_used: list[str] = Field(default_factory=list, examples=[["logs_tool", "metrics_tool", "health_tool"]])
    root_cause: str = Field(..., examples=["Database connections were exhausted in the API worker pool."])
    successful_fix: str | None = Field(default=None, examples=["restart_api_workers_simulation"])
    failed_fix: str | None = Field(default=None, examples=["generate_report"])
    confidence: str = Field(..., examples=["high"])
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
