from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.models.agent_step import AgentStep
from app.models.approval import ApprovalRequest
from app.models.incident import Incident
from app.schemas.enums import ApprovalStatus, IncidentStatus


router = APIRouter(tags=["metrics"])


def _gauge(name: str, value: int, labels: dict[str, str] | None = None) -> str:
    label_str = ""
    if labels:
        pairs = ",".join(f'{k}="{v}"' for k, v in labels.items())
        label_str = f"{{{pairs}}}"
    return f"{name}{label_str} {value}"


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrics",
    description=(
        "Exposes incident, agent step, and approval counts in Prometheus text format. "
        "No authentication is required so a Prometheus scraper can reach it without credentials."
    ),
    include_in_schema=True,
)
def get_metrics(db: Session = Depends(get_db_session)) -> str:
    lines: list[str] = []

    # incidents by status
    lines.append("# HELP opspilot_incidents_total Number of incidents grouped by status.")
    lines.append("# TYPE opspilot_incidents_total gauge")
    for status in IncidentStatus:
        count = db.query(Incident).filter(Incident.status == status).count()
        lines.append(_gauge("opspilot_incidents_total", count, {"status": status.value}))

    # total incidents
    lines.append("# HELP opspilot_incidents_all_total Total number of incidents across all statuses.")
    lines.append("# TYPE opspilot_incidents_all_total gauge")
    lines.append(_gauge("opspilot_incidents_all_total", db.query(Incident).count()))

    # agent steps by type
    lines.append("# HELP opspilot_agent_steps_total Number of agent steps grouped by step type.")
    lines.append("# TYPE opspilot_agent_steps_total gauge")
    step_types = [
        "triage", "tool_selection", "memory_lookup", "tool_call",
        "diagnosis", "remediation_recommendation", "policy_decision",
        "remediation_execution", "final_report",
    ]
    for step_type in step_types:
        count = db.query(AgentStep).filter(AgentStep.type == step_type).count()
        lines.append(_gauge("opspilot_agent_steps_total", count, {"type": step_type}))

    # approvals by status
    lines.append("# HELP opspilot_approvals_total Number of approval requests grouped by status.")
    lines.append("# TYPE opspilot_approvals_total gauge")
    for status in ApprovalStatus:
        count = db.query(ApprovalRequest).filter(ApprovalRequest.status == status).count()
        lines.append(_gauge("opspilot_approvals_total", count, {"status": status.value}))

    return "\n".join(lines) + "\n"
