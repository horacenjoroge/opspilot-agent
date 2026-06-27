"""add webhook_tokens table

Revision ID: 0004_webhook_tokens
Revises: 0003_agent_step_title
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_webhook_tokens"
down_revision = "0003_agent_step_title"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "webhook_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token", sa.Text(), nullable=False, unique=True, index=True),
        sa.Column("created_by", sa.String(), nullable=False, server_default="admin"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("incident_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("webhook_tokens")
