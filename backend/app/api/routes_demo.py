from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.schemas.incident import IncidentRead
from app.services.demo import DemoScenarioNotFoundError, DemoService
from app.services.incidents import IncidentService


router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/incidents/{scenario_name}", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_demo_incident(scenario_name: str, db: Session = Depends(get_db_session)) -> IncidentRead:
    try:
        incident = DemoService(IncidentService(db)).create_demo_incident(scenario_name)
    except DemoScenarioNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IncidentRead.model_validate(incident)
