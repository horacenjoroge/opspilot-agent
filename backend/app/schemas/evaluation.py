from pydantic import BaseModel, Field

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
