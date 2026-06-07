from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.incident_agent import IncidentAgent
from app.api.dependencies import get_db_session
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdateStatus
from app.schemas.timeline import TimelineItem
from app.services.incidents import IncidentNotFoundError, IncidentService
from app.services.timeline import TimelineService


router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_incident(payload: IncidentCreate, db: Session = Depends(get_db_session)) -> IncidentRead:
    incident = IncidentService(db).create_incident(payload)
    return IncidentRead.model_validate(incident)


@router.get("", response_model=list[IncidentRead])
async def list_incidents(db: Session = Depends(get_db_session)) -> list[IncidentRead]:
    incidents = IncidentService(db).list_incidents()
    return [IncidentRead.model_validate(incident) for incident in incidents]


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: int, db: Session = Depends(get_db_session)) -> IncidentRead:
    try:
        incident = IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IncidentRead.model_validate(incident)


@router.patch("/{incident_id}/status", response_model=IncidentRead)
async def update_incident_status(
    incident_id: int,
    payload: IncidentUpdateStatus,
    db: Session = Depends(get_db_session),
) -> IncidentRead:
    try:
        incident = IncidentService(db).update_status(incident_id, payload.status)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IncidentRead.model_validate(incident)


@router.post("/{incident_id}/run-agent")
async def run_incident_agent(incident_id: int, db: Session = Depends(get_db_session)) -> dict:
    try:
        IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return await IncidentAgent(db).run(incident_id)


@router.get("/{incident_id}/timeline", response_model=list[TimelineItem])
async def get_incident_timeline(incident_id: int, db: Session = Depends(get_db_session)) -> list[TimelineItem]:
    try:
        IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TimelineService(db).build_incident_timeline(incident_id)
