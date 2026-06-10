from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta


class TimelineItem(BaseModel):
    occurred_at: datetime = Field(..., examples=["2026-06-07T10:15:00Z"])
    category: str = Field(..., examples=["agent_step"])
    label: str = Field(..., examples=["triage"])
    status: str = Field(..., examples=["success"])
    details: dict[str, Any] = Field(default_factory=dict)


class TimelineListResponse(BaseModel):
    items: list[TimelineItem] = Field(default_factory=list)
    meta: PaginationMeta
