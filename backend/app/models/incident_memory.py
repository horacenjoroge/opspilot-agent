from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentMemory(Base):
    __tablename__ = "incident_memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"), nullable=False, unique=True, index=True)
    incident_type: Mapped[str] = mapped_column(nullable=False, index=True)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    tools_used: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    successful_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(nullable=False, default="medium")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident = relationship("Incident", back_populates="memory")
