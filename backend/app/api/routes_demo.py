from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth_dependencies import OPERATOR_ROLES, require_roles
from app.api.dependencies import get_db_session
from app.schemas.common import ErrorResponse
from app.schemas.incident import IncidentRead
from app.services.demo import DemoScenarioNotFoundError, DemoService
from app.services.incidents import IncidentService


router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post(
    "/incidents/{scenario_name}",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create seeded demo incident",
    description="Create a deterministic demo incident for a supported scenario such as high API error rate or queue backlog.",
    responses={404: {"model": ErrorResponse, "description": "Scenario name was not recognized."}},
)
async def create_demo_incident(
    scenario_name: str,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*OPERATOR_ROLES)),
) -> IncidentRead:
    try:
        incident = DemoService(IncidentService(db)).create_demo_incident(scenario_name)
    except DemoScenarioNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IncidentRead.model_validate(incident)
