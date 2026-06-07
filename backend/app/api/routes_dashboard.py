from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.evals.cases import EVAL_CASES
from app.schemas.enums import ApprovalStatus, IncidentStatus
from app.services.approvals import ApprovalService
from app.services.evaluations import EvaluationService
from app.services.incident_memory import IncidentMemoryService
from app.services.incidents import IncidentNotFoundError, IncidentService
from app.services.timeline import TimelineService
from app.ui import TEMPLATES_DIR


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    incidents = IncidentService(db).list_incidents()
    approvals = ApprovalService(db).list_requests()
    counts = {
        "incidents": len(incidents),
        "pending_approvals": len([item for item in approvals if item.status == ApprovalStatus.pending]),
        "active_incidents": len([item for item in incidents if item.status != IncidentStatus.resolved]),
    }
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "counts": counts,
            "recent_incidents": incidents[:5],
        },
    )


@router.get("/incidents", response_class=HTMLResponse)
async def dashboard_incidents(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    incidents = IncidentService(db).list_incidents()
    return templates.TemplateResponse(request, "incidents.html", {"incidents": incidents})


@router.get("/incidents/{incident_id}", response_class=HTMLResponse)
async def dashboard_incident_detail(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    try:
        incident = IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    approvals = [item for item in ApprovalService(db).list_requests() if item.incident_id == incident_id]
    timeline = TimelineService(db).build_incident_timeline(incident_id)
    used_memories = IncidentMemoryService(db).list_used_for_incident(incident_id)
    return templates.TemplateResponse(
        request,
        "incident_detail.html",
        {
            "incident": incident,
            "approvals": approvals,
            "timeline": timeline,
            "used_memories": used_memories,
        },
    )


@router.get("/approvals", response_class=HTMLResponse)
async def dashboard_approvals(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    approvals = ApprovalService(db).list_requests()
    return templates.TemplateResponse(request, "approvals.html", {"approvals": approvals})


@router.get("/demo", response_class=HTMLResponse)
async def dashboard_demo(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    incidents = IncidentService(db).list_incidents()
    scenarios = [
        "high_api_error_rate",
        "queue_backlog",
        "database_latency",
        "ambiguous_alert",
        "tool_failure",
    ]
    return templates.TemplateResponse(
        request,
        "demo.html",
        {
            "scenarios": scenarios,
            "recent_demo_incidents": [incident for incident in incidents if incident.source.startswith("demo:")][:8],
        },
    )


@router.get("/evals", response_class=HTMLResponse)
async def dashboard_evaluations(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    cases = [case["scenario"] for case in EVAL_CASES]
    return templates.TemplateResponse(
        request,
        "evals.html",
        {
            "cases": cases,
        },
    )
