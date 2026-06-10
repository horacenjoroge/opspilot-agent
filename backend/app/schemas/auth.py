from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import UserRole


class UserRead(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str = Field(..., examples=["admin@opspilot.local"])
    password: str = Field(..., min_length=8, examples=["change-me-now"])


class LoginResponse(BaseModel):
    user: UserRead
    session_expires_at: datetime
    auth_enabled: bool = True


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    dashboard_auth_enabled: bool
    user: UserRead | None = None
