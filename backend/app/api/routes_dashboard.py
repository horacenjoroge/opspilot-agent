from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.auth_dependencies import resolve_optional_auth_context
from app.api.dependencies import get_db_session
from app.core.config import get_settings
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

SCENARIO_CARDS = {
    "high_api_error_rate": {
        "title": "High API error rate",
        "description": "Recommended scenario for seeing triage, evidence gathering, a dangerous remediation recommendation, and human approval in one flow.",
        "recommended": True,
    },
    "queue_backlog": {
        "title": "Queue backlog",
        "description": "Demonstrates worker saturation and approval-gated remediation from metrics-heavy evidence.",
        "recommended": False,
    },
    "database_latency": {
        "title": "Database latency spike",
        "description": "Best scenario for a clean end-to-end resolution without approval, including final report and memory save.",
        "recommended": False,
    },
    "ambiguous_alert": {
        "title": "Ambiguous alert",
        "description": "Shows that the agent can stay cautious when evidence is weak and choose a safer report-oriented path.",
        "recommended": False,
    },
    "tool_failure": {
        "title": "Tool failure",
        "description": "Highlights fallback behavior when investigation tooling is incomplete or unavailable.",
        "recommended": False,
    },
}

ARCHITECTURE_STEPS = [
    "Incident created",
    "Triage",
    "Tool selection",
    "Evidence collection",
    "Memory retrieval",
    "Diagnosis",
    "Remediation recommendation",
    "Policy decision",
    "Human approval if risky",
    "Final report",
    "Memory saved",
]


def _dashboard_context(request: Request, db: Session) -> dict:
    settings = get_settings()
    auth_context = resolve_optional_auth_context(request, db)
    app_display_name = "OpsPilot" if settings.app_name.lower() == "opspilot" else settings.app_name
    provider_label = "Qwen Cloud" if settings.llm_provider == "qwen" else "Provider unavailable"
    provider_mode = "Qwen active" if settings.llm_provider == "qwen" else "Provider unavailable"
    return {
        "request": request,
        "app_name": app_display_name,
        "llm_provider": settings.llm_provider,
        "provider_label": provider_label,
        "provider_mode": provider_mode,
        "tools_notice": "Controlled infrastructure adapters",
        "environment_label": settings.app_env,
        "human_approval_label": "enabled",
        "auth_enabled": settings.enable_auth,
        "dashboard_auth_enabled": settings.enable_dashboard_auth,
        "current_user": auth_context.user,
        "current_user_name": auth_context.display_name,
        "current_user_role": auth_context.role.value,
        "banner_text": (
            f"OpsPilot — SRE Autopilot Agent · Qwen Cloud Hackathon Track 4 · "
            f"Provider: {provider_label} · Tool allowlist enforced · Approval gate active"
        ),
    }


def _require_dashboard_access(request: Request, db: Session) -> RedirectResponse | None:
    settings = get_settings()
    if not (settings.enable_auth and settings.enable_dashboard_auth):
        return None
    auth_context = resolve_optional_auth_context(request, db)
    if auth_context.user is not None:
        return None
    next_path = request.url.path
    if request.url.query:
        next_path = f"{next_path}?{request.url.query}"
    return RedirectResponse(url=f"/login?next={quote(next_path)}", status_code=status.HTTP_303_SEE_OTHER)


def _latest_timeline_item(timeline: list, label: str):
    for item in reversed(timeline):
        if item.label == label:
            return item
    return None


def _group_approvals(approvals: list) -> dict[str, list]:
    return {
        "pending": [item for item in approvals if item.status == ApprovalStatus.pending],
        "approved": [item for item in approvals if item.status == ApprovalStatus.approved],
        "rejected": [item for item in approvals if item.status == ApprovalStatus.rejected],
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    redirect = _require_dashboard_access(request, db)
    if redirect is not None:
        return redirect
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
            **_dashboard_context(request, db),
            "counts": counts,
            "recent_incidents": incidents[:5],
            "how_to_use_steps": [
                "Go to Demo and create the high_api_error_rate incident.",
                "Open the incident and click Run Agent — Qwen triages and collects evidence.",
                "Watch the backend classify the recommended action as dangerous and block it.",
                "Go to Approvals and approve or reject the blocked action.",
                "Go to Evaluations and run the full suite to see structured pass/fail checks.",
            ],
            "recommended_flow": [
                "The model never calls a tool directly — the backend allowlist decides what runs.",
                "Risk classification (safe / medium / dangerous) is enforced by policy, not the model.",
                "Dangerous actions create an approval request; the model cannot bypass this gate.",
                "Every triage step, tool call, policy decision, and approval is stored as a timeline event.",
                "Evaluations replay the same workflow and assert expected severity, tools, and final status.",
            ],
        },
    )


@router.get("/incidents", response_class=HTMLResponse)
async def dashboard_incidents(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    redirect = _require_dashboard_access(request, db)
    if redirect is not None:
        return redirect
    incidents = IncidentService(db).list_incidents()
    return templates.TemplateResponse(
        request,
        "incidents.html",
        {
            **_dashboard_context(request, db),
            "incidents": incidents,
        },
    )


@router.get("/incidents/{incident_id}", response_class=HTMLResponse)
async def dashboard_incident_detail(
    incident_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    redirect = _require_dashboard_access(request, db)
    if redirect is not None:
        return redirect
    try:
        incident = IncidentService(db).get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    approvals = [item for item in ApprovalService(db).list_requests() if item.incident_id == incident_id]
    timeline = TimelineService(db).build_incident_timeline(incident_id)
    used_memories = IncidentMemoryService(db).list_used_for_incident(incident_id)
    evidence_items = [item for item in timeline if item.category == "agent_step" and item.details.get("tool_name")]
    approval_groups = _group_approvals(approvals)
    policy_item = _latest_timeline_item(timeline, "policy_decision")
    diagnosis_item = _latest_timeline_item(timeline, "diagnosis")
    remediation_item = _latest_timeline_item(timeline, "remediation_recommendation")
    final_report_item = _latest_timeline_item(timeline, "final_report")
    memory_saved_item = _latest_timeline_item(timeline, "memory_saved")
    return templates.TemplateResponse(
        request,
        "incident_detail.html",
        {
            **_dashboard_context(request, db),
            "incident": incident,
            "approvals": approvals,
            "approval_groups": approval_groups,
            "timeline": timeline,
            "used_memories": used_memories,
            "saved_memory": incident.memory,
            "evidence_items": evidence_items,
            "policy_item": policy_item,
            "diagnosis_item": diagnosis_item,
            "remediation_item": remediation_item,
            "final_report_item": final_report_item,
            "memory_saved_item": memory_saved_item,
        },
    )


@router.get("/approvals", response_class=HTMLResponse)
async def dashboard_approvals(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    redirect = _require_dashboard_access(request, db)
    if redirect is not None:
        return redirect
    approvals = ApprovalService(db).list_requests()
    return templates.TemplateResponse(
        request,
        "approvals.html",
        {
            **_dashboard_context(request, db),
            "approvals": approvals,
            "approval_groups": _group_approvals(approvals),
        },
    )


@router.get("/demo", response_class=HTMLResponse)
async def dashboard_demo(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    redirect = _require_dashboard_access(request, db)
    if redirect is not None:
        return redirect
    incidents = IncidentService(db).list_incidents()
    return templates.TemplateResponse(
        request,
        "demo.html",
        {
            **_dashboard_context(request, db),
            "scenarios": [
                {"key": key, **value}
                for key, value in SCENARIO_CARDS.items()
            ],
            "recent_demo_incidents": [incident for incident in incidents if incident.source.startswith("demo:")][:8],
        },
    )


@router.get("/evals", response_class=HTMLResponse)
async def dashboard_evaluations(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    redirect = _require_dashboard_access(request, db)
    if redirect is not None:
        return redirect
    cases = [case["scenario"] for case in EVAL_CASES]
    evaluation_service = EvaluationService(IncidentService(db))
    latest_run = evaluation_service.latest_run()
    history = evaluation_service.list_history(limit=5, offset=0)
    return templates.TemplateResponse(
        request,
        "evals.html",
        {
            **_dashboard_context(request, db),
            "cases": cases,
            "scenario_cards": [SCENARIO_CARDS.get(case, {"title": case.replace("_", " ").title(), "description": ""}) for case in cases],
            "historical_eval_placeholder": "Historical eval trends will appear after persistence is enabled.",
            "latest_eval_run": latest_run,
            "eval_history_items": history.items,
        },
    )


@router.get("/architecture", response_class=HTMLResponse)
async def dashboard_architecture(request: Request, db: Session = Depends(get_db_session)) -> HTMLResponse:
    redirect = _require_dashboard_access(request, db)
    if redirect is not None:
        return redirect
    return templates.TemplateResponse(
        request,
        "architecture.html",
        {
            **_dashboard_context(request, db),
            "workflow_steps": ARCHITECTURE_STEPS,
            "simulated_components": [
                "Infrastructure tools currently use seeded evidence instead of touching live production systems.",
                "Remediation actions stay non-destructive and never directly control real infrastructure.",
                "Notification behavior is currently kept local and non-destructive.",
            ],
            "production_shaped_components": [
                "FastAPI backend with thin routes and service-layer orchestration.",
                "Strict JSON model contracts validated by Pydantic.",
                "Persistent incidents, approvals, audit logs, agent steps, and memory records.",
                "Docker plus Nginx deployment shape for ECS-style hosting.",
            ],
        },
    )
