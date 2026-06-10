from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.core.config import get_settings
from app.models.user import User
from app.schemas.enums import UserRole
from app.services.auth import AuthContext, AuthService, auth_disabled_context


READ_ROLES = (UserRole.admin, UserRole.operator, UserRole.reviewer, UserRole.viewer)
OPERATOR_ROLES = (UserRole.admin, UserRole.operator)
REVIEWER_ROLES = (UserRole.admin, UserRole.reviewer)


def _extract_session_token(request: Request) -> str | None:
    settings = get_settings()
    cookie_token = request.cookies.get(settings.auth_session_cookie_name)
    if cookie_token:
        return cookie_token
    authorization = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if authorization.startswith(prefix):
        return authorization[len(prefix):].strip()
    return None


def resolve_optional_auth_context(request: Request, db: Session) -> AuthContext:
    settings = get_settings()
    if not settings.enable_auth:
        return auth_disabled_context()
    token = _extract_session_token(request)
    if not token:
        return AuthContext(auth_enabled=True, role=UserRole.viewer, user=None, source="anonymous")
    user = AuthService(db).get_session_user(token)
    if user is None:
        return AuthContext(auth_enabled=True, role=UserRole.viewer, user=None, source="expired")
    request.state.current_user = user
    return AuthContext(auth_enabled=True, role=user.role, user=user, source="session")


def get_current_auth_context(
    request: Request,
    db: Session = Depends(get_db_session),
) -> AuthContext:
    context = resolve_optional_auth_context(request, db)
    if context.auth_enabled and context.user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return context


def get_current_user(
    context: AuthContext = Depends(get_current_auth_context),
) -> User | None:
    return context.user


def require_roles(*allowed_roles: UserRole) -> Callable[[AuthContext], AuthContext]:
    def dependency(context: AuthContext = Depends(get_current_auth_context)) -> AuthContext:
        if not context.auth_enabled:
            return context
        if context.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return context

    return dependency
