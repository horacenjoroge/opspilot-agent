from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ToolStatus


class AgentStepCreate(BaseModel):
    incident_id: int = Field(..., examples=[1])
    step_number: int = Field(..., examples=[1])
    type: str = Field(..., examples=["tool_call"])
    tool_name: str | None = Field(default=None, examples=["logs_tool"])
    input_json: dict | None = Field(default=None, examples=[{"query": "db connection errors"}])
    output_json: dict | None = Field(default=None, examples=[{"errors": ["too many clients already"]}])
    model_summary: str | None = Field(default=None, examples=["Fetched relevant log lines for the alert window."])
    status: ToolStatus = Field(..., examples=["success"])


class AgentStepRead(AgentStepCreate):
    id: int = Field(..., examples=[1])
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
