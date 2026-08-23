from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgresql import Base


class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    alert_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    parent_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("parents.parent_id"),
        nullable=False,
        index=True,
    )

    rider_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("riders.rider_id"),
        nullable=False,
        index=True,
    )

    vehicle_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    device_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    incident_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("safety_events.id"),
        nullable=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )