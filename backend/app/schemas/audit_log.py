from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    id: int = Field(..., examples=[1])
    actor: str = Field(..., examples=["system"])
    action: str = Field(..., examples=["incident.created"])
    target_type: str = Field(..., examples=["incident"])
    target_id: str = Field(..., examples=["1"])
    metadata_json: dict = Field(..., examples=[{"severity": "high"}])
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
