from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta
from app.schemas.enums import IncidentStatus


class EvaluationCaseExpectation(BaseModel):
    scenario: str = Field(..., examples=["high_api_error_rate"])
    expected_severity: str = Field(..., examples=["high"])
    expected_tools: list[str] = Field(default_factory=list, examples=[["logs_tool", "metrics_tool"]])
    expected_requires_approval: bool = Field(..., examples=[True])
    expected_final_status: IncidentStatus = Field(..., examples=["waiting_for_approval"])
    expected_diagnosis_keywords: list[str] = Field(default_factory=list, examples=[["database", "exhaustion"]])


class EvaluationCaseResult(BaseModel):
    scenario: str = Field(..., examples=["high_api_error_rate"])
    passed: bool = Field(..., examples=[True])
    incident_id: int = Field(..., examples=[12])
    actual_severity: str = Field(..., examples=["high"])
    actual_tools: list[str] = Field(default_factory=list, examples=[["logs_tool", "metrics_tool"]])
    actual_requires_approval: bool = Field(..., examples=[True])
    actual_final_status: IncidentStatus = Field(..., examples=["waiting_for_approval"])
    diagnosis_text: str = Field(..., examples=["Database connections were exhausted in the application pool."])
    checks: dict[str, bool] = Field(default_factory=dict)
    expected: EvaluationCaseExpectation


class EvaluationRunSummary(BaseModel):
    total: int = Field(..., examples=[5])
    passed: int = Field(..., examples=[5])
    failed: int = Field(..., examples=[0])
    results: list[EvaluationCaseResult] = Field(default_factory=list)


class EvaluationHistoryItem(BaseModel):
    id: int = Field(..., examples=[1])
    provider: str = Field(..., examples=["mock"])
    status: str = Field(..., examples=["completed"])
    total_cases: int = Field(..., examples=[5])
    passed_cases: int = Field(..., examples=[5])
    failed_cases: int = Field(..., examples=[0])
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = Field(default=None, examples=[412])
    details_json: dict | None = None


class EvaluationCaseHistoryItem(BaseModel):
    id: int = Field(..., examples=[1])
    evaluation_run_id: int = Field(..., examples=[1])
    case_name: str = Field(..., examples=["high_api_error_rate"])
    status: str = Field(..., examples=["completed"])
    passed: bool = Field(..., examples=[True])
    score: int | None = Field(default=None, examples=[100])
    error_message: str | None = Field(default=None, examples=["Scenario execution failed."])
    details_json: dict | None = None
    created_at: datetime


class EvaluationHistoryResponse(BaseModel):
    items: list[EvaluationHistoryItem] = Field(default_factory=list)
    meta: PaginationMeta
