from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.incident_agent import IncidentAgent
from app.api.dependencies import get_db_session
from app.schemas.common import AgentRunResponse, ErrorResponse
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdateStatus
from app.schemas.timeline import TimelineItem
from app.services.incidents import IncidentNotFoundError, IncidentService
from app.services.timeline import TimelineService


router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create incident",
    description="Create a new incident record that can later be triaged by the agent workflow.",
)
async def create_incident(payload: IncidentCreate, db: Session = Depends(get_db_session)) -> IncidentRead:
    incident = IncidentService(db).create_incident(payload)
    return IncidentRead.model_validate(incident)


@router.get(
    "",
    response_model=list[IncidentRead],
    status_code=status.HTTP_200_OK,
    summary="List incidents",
    description="Return incidents ordered by newest first.",
)
async def list_incidents(db: Session = Depends(get_db_session)) -> list[IncidentRead]:
    incidents = IncidentService(db).list_incidents()
    return [IncidentRead.model_validate(incident) for incident in incidents]


@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
    status_code=status.HTTP_200_OK,
    summary="Get incident",
    description="Fetch a single incident including current status, diagnosis, recommended action, and final report if available.",
    responses={404: {"model": ErrorResponse, "description": "Incident was not found."}},
)
async def get_incident(incident_id: int, db: Session = Depends(get_db_session)) -> IncidentRead:
    try:
        incident = IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IncidentRead.model_validate(incident)


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentRead,
    status_code=status.HTTP_200_OK,
    summary="Update incident status",
    description="Manually update the incident lifecycle state.",
    responses={404: {"model": ErrorResponse, "description": "Incident was not found."}},
)
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


@router.post(
    "/{incident_id}/run-agent",
    response_model=AgentRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run incident agent",
    description=(
        "Execute the backend-controlled incident workflow. The agent performs Qwen-backed triage, "
        "tool selection, evidence gathering, diagnosis, remediation recommendation, policy evaluation, "
        "and final reporting or approval creation."
    ),
    responses={404: {"model": ErrorResponse, "description": "Incident was not found."}},
)
async def run_incident_agent(incident_id: int, db: Session = Depends(get_db_session)) -> AgentRunResponse:
    try:
        IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AgentRunResponse.model_validate(await IncidentAgent(db).run(incident_id))


@router.get(
    "/{incident_id}/timeline",
    response_model=list[TimelineItem],
    status_code=status.HTTP_200_OK,
    summary="Get incident timeline",
    description="Return the merged evidence-first timeline built from agent steps, approval records, and audit logs.",
    responses={404: {"model": ErrorResponse, "description": "Incident was not found."}},
)
async def get_incident_timeline(incident_id: int, db: Session = Depends(get_db_session)) -> list[TimelineItem]:
    try:
        IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TimelineService(db).build_incident_timeline(incident_id)
