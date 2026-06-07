from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.schemas.common import ErrorResponse
from app.schemas.evaluation import EvaluationCaseResult, EvaluationRunSummary
from app.services.evaluations import EvaluationService
from app.services.incidents import IncidentService


router = APIRouter(prefix="/api/evals", tags=["evaluations"])


@router.post(
    "/run",
    response_model=EvaluationRunSummary,
    status_code=status.HTTP_200_OK,
    summary="Run all evaluation scenarios",
    description="Execute all deterministic mock-backed evaluation scenarios and return PASS or FAIL results.",
)
async def run_all_evaluations(db: Session = Depends(get_db_session)) -> EvaluationRunSummary:
    service = EvaluationService(IncidentService(db))
    return await service.run_all()


@router.post(
    "/run/{scenario_name}",
    response_model=EvaluationCaseResult,
    status_code=status.HTTP_200_OK,
    summary="Run one evaluation scenario",
    description="Execute one deterministic evaluation scenario and return the expected-versus-actual outcome summary.",
    responses={404: {"model": ErrorResponse, "description": "Scenario name was not recognized."}},
)
async def run_single_evaluation(scenario_name: str, db: Session = Depends(get_db_session)) -> EvaluationCaseResult:
    service = EvaluationService(IncidentService(db))
    try:
        return await service.run_case(scenario_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
