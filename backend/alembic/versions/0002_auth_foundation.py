"""add users and sessions for auth foundation

Revision ID: 0002_auth_foundation
Revises: 0001_initial_schema
Create Date: 2026-06-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_auth_foundation"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=512), nullable=True),
        sa.Column("role", sa.Enum("admin", "operator", "reviewer", "viewer", name="user_role_enum"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role_is_active", "users", ["role", "is_active"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_token"),
    )
    op.create_index("ix_user_sessions_id", "user_sessions", ["id"])
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_session_token", "user_sessions", ["session_token"])
    op.create_index("ix_user_sessions_user_id_expires_at", "user_sessions", ["user_id", "expires_at"])


def downgrade() -> None:
    op.drop_index("ix_user_sessions_user_id_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_session_token", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_index("ix_user_sessions_id", table_name="user_sessions")
    op.drop_table("user_sessions")

    op.drop_index("ix_users_role_is_active", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
