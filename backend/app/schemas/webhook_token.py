from datetime import datetime

from pydantic import BaseModel, Field


class WebhookTokenCreate(BaseModel):
    name: str = Field(..., examples=["Alertmanager prod"])
    created_by: str = Field(default="admin", examples=["admin"])


class WebhookTokenRead(BaseModel):
    id: int
    name: str
    created_by: str
    active: bool
    incident_count: int
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookTokenCreated(WebhookTokenRead):
    token: str = Field(..., description="Raw token value — shown only once.")
