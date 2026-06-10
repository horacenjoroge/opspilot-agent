from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User, UserSession
from app.schemas.enums import UserRole


class AuthenticationError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


@dataclass(slots=True)
class AuthContext:
    auth_enabled: bool
    role: UserRole
    user: User | None = None
    source: str = "session"

    @property
    def is_authenticated(self) -> bool:
        return self.user is not None

    @property
    def display_name(self) -> str:
        if self.user is not None:
            return self.user.name
        if self.auth_enabled:
            return "Guest"
        return "Demo Admin"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 390000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${derived.hex()}"


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    try:
        algorithm, iterations_str, salt, stored = hashed_password.split("$", 3)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations_str),
    )
    return hmac.compare_digest(derived.hex(), stored)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())))

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == normalize_email(email)))

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def create_user(
        self,
        *,
        email: str,
        name: str,
        role: UserRole,
        password: str | None = None,
        is_active: bool = True,
    ) -> User:
        normalized_email = normalize_email(email)
        if self.get_user_by_email(normalized_email):
            raise UserAlreadyExistsError(f"User with email '{normalized_email}' already exists.")
        user = User(
            email=normalized_email,
            name=name.strip(),
            hashed_password=hash_password(password) if password else None,
            role=role,
            is_active=is_active,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.get_user_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")
        user.last_login_at = datetime.now(timezone.utc)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_session(self, user: User) -> UserSession:
        ttl = timedelta(hours=self.settings.auth_session_ttl_hours)
        session = UserSession(
            user_id=user.id,
            session_token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + ttl,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def revoke_session(self, token: str) -> None:
        session = self.db.scalar(select(UserSession).where(UserSession.session_token == token))
        if session is None:
            return
        self.db.delete(session)
        self.db.commit()

    def get_session_user(self, token: str) -> User | None:
        session = self.db.scalar(select(UserSession).where(UserSession.session_token == token))
        if session is None:
            return None
        now = datetime.now(timezone.utc)
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            self.db.delete(session)
            self.db.commit()
            return None
        user = self.get_user_by_id(session.user_id)
        if user is None or not user.is_active:
            return None
        session.last_seen_at = now
        self.db.add(session)
        self.db.commit()
        return user

    def seed_dev_admin(self, *, email: str, password: str, name: str = "OpsPilot Admin") -> User:
        user = self.get_user_by_email(email)
        hashed = hash_password(password)
        if user is None:
            return self.create_user(email=email, name=name, role=UserRole.admin, password=password, is_active=True)
        user.name = name
        user.role = UserRole.admin
        user.is_active = True
        user.hashed_password = hashed
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


def auth_disabled_context() -> AuthContext:
    return AuthContext(auth_enabled=False, role=UserRole.admin, user=None, source="demo")
