import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.agents.incident_agent import IncidentAgent
from app.api.dependencies import get_db_session
from app.db.session import SessionLocal
from app.schemas.enums import Severity
from app.schemas.incident import IncidentCreate
from app.services.incidents import IncidentService

logger = logging.getLogger("opspilot.webhooks")

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.critical,
    "high": Severity.high,
    "error": Severity.high,
    "warning": Severity.medium,
    "warn": Severity.medium,
    "medium": Severity.medium,
    "low": Severity.low,
    "info": Severity.low,
}


async def _run_agent_background(incident_id: int) -> None:
    db = SessionLocal()
    try:
        await IncidentAgent(db).run(incident_id)
    except Exception as exc:
        logger.error("Background agent run failed for incident %d: %s", incident_id, exc)
    finally:
        db.close()


def _map_severity(raw: str) -> Severity:
    return _SEVERITY_MAP.get(raw.strip().lower(), Severity.medium)


@router.post(
    "/alertmanager",
    status_code=202,
    summary="Alertmanager webhook",
    description=(
        "Accepts Prometheus Alertmanager webhook payloads. Each firing alert becomes one incident. "
        "Pass ?auto_run=true to immediately start the agent on every created incident."
    ),
)
async def ingest_alertmanager(
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
    auto_run: bool = Query(default=False, description="Start the agent automatically after creating each incident."),
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    alerts = payload.get("alerts", [])
    created_ids: list[int] = []

    for alert in alerts:
        if alert.get("status") != "firing":
            continue
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        title = labels.get("alertname", "Unnamed Alert")
        severity_raw = labels.get("severity", "medium")
        description = (
            annotations.get("description")
            or annotations.get("summary")
            or f"Alert fired: {title}"
        )
        job = labels.get("job") or labels.get("service") or "unknown"
        source = f"alertmanager:{job}"

        incident = IncidentService(db).create_incident(
            IncidentCreate(
                title=title,
                description=description,
                severity=_map_severity(severity_raw),
                source=source,
            )
        )
        created_ids.append(incident.id)
        if auto_run:
            background_tasks.add_task(_run_agent_background, incident.id)
        logger.info("alertmanager webhook created incident=%d auto_run=%s", incident.id, auto_run)

    return {"created_incidents": created_ids, "count": len(created_ids), "auto_run": auto_run}


@router.post(
    "/generic",
    status_code=202,
    summary="Generic webhook",
    description=(
        "Accepts any JSON payload with title, severity, description, and source fields. "
        "Compatible with Datadog, Grafana, PagerDuty, or any custom alerting tool. "
        "Pass ?auto_run=true to immediately start the agent."
    ),
)
async def ingest_generic(
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
    auto_run: bool = Query(default=False, description="Start the agent automatically after creating the incident."),
    db: Session = Depends(get_db_session),
) -> dict[str, Any]:
    title = payload.get("title") or payload.get("name") or payload.get("alertname") or "Unnamed Alert"
    severity_raw = str(payload.get("severity") or payload.get("level") or payload.get("priority") or "medium")
    description = (
        payload.get("description")
        or payload.get("message")
        or payload.get("summary")
        or payload.get("body")
        or f"Alert: {title}"
    )
    source = str(payload.get("source") or payload.get("origin") or payload.get("generator") or "webhook")

    incident = IncidentService(db).create_incident(
        IncidentCreate(
            title=title,
            description=description,
            severity=_map_severity(severity_raw),
            source=source,
        )
    )
    if auto_run:
        background_tasks.add_task(_run_agent_background, incident.id)
    logger.info("generic webhook created incident=%d auto_run=%s", incident.id, auto_run)

    return {
        "incident_id": incident.id,
        "status": "triaging" if auto_run else "new",
        "auto_run": auto_run,
        "view_url": f"/incidents/{incident.id}",
    }
