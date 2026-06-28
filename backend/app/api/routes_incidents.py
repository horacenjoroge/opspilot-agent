import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

logger = logging.getLogger("opspilot.api")

from app.agents.incident_agent import IncidentAgent
from app.api.auth_dependencies import OPERATOR_ROLES, READ_ROLES, require_roles
from app.api.dependencies import get_db_session
from app.schemas.common import AgentRunResponse, ErrorResponse
from app.schemas.incident import IncidentCreate, IncidentListResponse, IncidentRead, IncidentUpdateStatus
from app.schemas.enums import IncidentStatus, Severity
from app.schemas.timeline import TimelineItem, TimelineListResponse
from app.db.session import SessionLocal
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
async def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*OPERATOR_ROLES)),
) -> IncidentRead:
    incident = IncidentService(db).create_incident(payload)
    return IncidentRead.model_validate(incident)


@router.get(
    "",
    response_model=list[IncidentRead] | IncidentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List incidents",
    description="Return incidents ordered by newest first, with optional filtering and pagination metadata.",
)
async def list_incidents(
    db: Session = Depends(get_db_session),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    status_filter: IncidentStatus | None = Query(default=None, alias="status"),
    severity: Severity | None = None,
    source: str | None = Query(default=None, description="Source type filter: demo, alertmanager, grafana, webhook"),
    include_meta: bool = False,
    _: object = Depends(require_roles(*READ_ROLES)),
) -> list[IncidentRead] | IncidentListResponse:
    service = IncidentService(db)
    incidents = service.list_incidents(
        limit=limit,
        offset=offset,
        status=status_filter,
        severity=severity,
        source_filter=source,
    )
    items = [IncidentRead.model_validate(incident) for incident in incidents]
    if not include_meta:
        return items
    return IncidentListResponse(
        items=items,
        meta={
            "total": service.count_incidents(status=status_filter, severity=severity, source_filter=source),
            "limit": limit,
            "offset": offset,
        },
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
    status_code=status.HTTP_200_OK,
    summary="Get incident",
    description="Fetch a single incident including current status, diagnosis, recommended action, and final report if available.",
    responses={404: {"model": ErrorResponse, "description": "Incident was not found."}},
)
async def get_incident(
    incident_id: int,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*READ_ROLES)),
) -> IncidentRead:
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
    _: object = Depends(require_roles(*OPERATOR_ROLES)),
) -> IncidentRead:
    try:
        incident = IncidentService(db).update_status(incident_id, payload.status)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return IncidentRead.model_validate(incident)


async def _run_agent_background(incident_id: int) -> None:
    db = SessionLocal()
    try:
        await IncidentAgent(db).run(incident_id)
    except Exception as exc:
        logger.error("Background agent run failed for incident %d: %s", incident_id, exc)
    finally:
        db.close()


@router.post(
    "/{incident_id}/run-agent",
    response_model=AgentRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run incident agent",
    description=(
        "Enqueues the incident agent workflow as a background task and returns immediately. "
        "Poll GET /api/incidents/{incident_id} until status is no longer 'triaging' to get the result."
    ),
    responses={404: {"model": ErrorResponse, "description": "Incident was not found."}},
)
async def run_incident_agent(
    incident_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*OPERATOR_ROLES)),
) -> AgentRunResponse:
    try:
        IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    background_tasks.add_task(_run_agent_background, incident_id)
    return AgentRunResponse(incident_id=incident_id, status="triaging", recommended_action=None)


@router.get(
    "/{incident_id}/timeline",
    response_model=list[TimelineItem] | TimelineListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get incident timeline",
    description="Return the merged evidence-first timeline built from agent steps, approval records, and audit logs.",
    responses={404: {"model": ErrorResponse, "description": "Incident was not found."}},
)
async def get_incident_timeline(
    incident_id: int,
    db: Session = Depends(get_db_session),
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_meta: bool = False,
    _: object = Depends(require_roles(*READ_ROLES)),
) -> list[TimelineItem] | TimelineListResponse:
    try:
        IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    service = TimelineService(db)
    items = service.build_incident_timeline(incident_id, limit=limit, offset=offset)
    if not include_meta:
        return items
    return TimelineListResponse(
        items=items,
        meta={
            "total": service.count_incident_timeline_items(incident_id),
            "limit": limit,
            "offset": offset,
        },
    )
