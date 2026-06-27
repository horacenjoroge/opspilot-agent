import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.webhook_token import WebhookToken
from app.schemas.webhook_token import WebhookTokenCreate


def _generate_token() -> str:
    return f"opspilot_wh_{secrets.token_urlsafe(32)}"


class WebhookTokenService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: WebhookTokenCreate) -> tuple[WebhookToken, str]:
        raw_token = _generate_token()
        record = WebhookToken(
            name=payload.name,
            token=raw_token,
            created_by=payload.created_by,
            active=True,
            incident_count=0,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record, raw_token

    def list_tokens(self) -> list[WebhookToken]:
        return self.db.query(WebhookToken).order_by(WebhookToken.created_at.desc()).all()

    def revoke(self, token_id: int) -> WebhookToken | None:
        record = self.db.get(WebhookToken, token_id)
        if record is None:
            return None
        record.active = False
        self.db.commit()
        return record

    def verify(self, raw_token: str) -> WebhookToken | None:
        record = (
            self.db.query(WebhookToken)
            .filter(WebhookToken.token == raw_token, WebhookToken.active == True)  # noqa: E712
            .first()
        )
        if record is None:
            return None
        record.last_used_at = datetime.now(timezone.utc)
        record.incident_count += 1
        self.db.commit()
        return record
