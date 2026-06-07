from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.schemas.enums import RiskLevel, ToolStatus


class ToolError(BaseModel):
    code: str = Field(..., examples=["approval_required"])
    message: str = Field(..., examples=["Human approval is required before running this action."])
    details: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    status: ToolStatus = Field(..., examples=["success"])
    data: dict[str, Any] = Field(default_factory=dict)
    summary: str = Field(..., examples=["Collected deployment context for the incident scenario."])
    error: ToolError | None = None


class ToolExecutionError(Exception):
    def __init__(self, *, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class BaseTool(ABC):
    name: str
    description: str
    risk_level: RiskLevel
    input_schema: type[BaseModel]

    async def execute(self, payload: dict[str, Any]) -> ToolResult:
        try:
            validated_payload = self.input_schema.model_validate(payload)
            return await self.run(validated_payload)
        except ValidationError as exc:
            return ToolResult(
                status=ToolStatus.failed,
                data={},
                summary=f"{self.name} rejected the input payload.",
                error=ToolError(code="invalid_input", message="Tool input failed validation.", details={"errors": exc.errors()}),
            )
        except ToolExecutionError as exc:
            return ToolResult(
                status=ToolStatus.failed,
                data={},
                summary=f"{self.name} could not complete the request.",
                error=ToolError(code=exc.code, message=exc.message, details=exc.details),
            )

    @abstractmethod
    async def run(self, payload: BaseModel) -> ToolResult:
        raise NotImplementedError
