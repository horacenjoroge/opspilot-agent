from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth_dependencies import OPERATOR_ROLES, require_roles
from app.api.dependencies import get_db_session
from app.schemas.webhook_token import WebhookTokenCreate, WebhookTokenCreated, WebhookTokenRead
from app.services.webhook_tokens import WebhookTokenService

router = APIRouter(prefix="/api/webhook-tokens", tags=["webhook-tokens"])


@router.post(
    "",
    response_model=WebhookTokenCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook token",
    description="Creates a new webhook token. The raw token value is returned once and never stored in plain text again.",
)
async def create_token(
    payload: WebhookTokenCreate,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*OPERATOR_ROLES)),
) -> WebhookTokenCreated:
    record, raw_token = WebhookTokenService(db).create(payload)
    return WebhookTokenCreated(
        id=record.id,
        name=record.name,
        created_by=record.created_by,
        active=record.active,
        incident_count=record.incident_count,
        last_used_at=record.last_used_at,
        created_at=record.created_at,
        token=raw_token,
    )


@router.get(
    "",
    response_model=list[WebhookTokenRead],
    status_code=status.HTTP_200_OK,
    summary="List webhook tokens",
)
async def list_tokens(
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*OPERATOR_ROLES)),
) -> list[WebhookTokenRead]:
    return [WebhookTokenRead.model_validate(t) for t in WebhookTokenService(db).list_tokens()]


@router.delete(
    "/{token_id}",
    status_code=status.HTTP_200_OK,
    summary="Revoke webhook token",
)
async def revoke_token(
    token_id: int,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*OPERATOR_ROLES)),
) -> dict:
    record = WebhookTokenService(db).revoke(token_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found.")
    return {"id": record.id, "active": record.active}
