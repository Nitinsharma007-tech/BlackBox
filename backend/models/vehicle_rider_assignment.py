from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgresql import Base


class VehicleRiderAssignment(Base):
    __tablename__ = "vehicle_rider_assignments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    vehicle_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("vehicles.vehicle_id"),
        nullable=False,
        index=True,
    )

    rider_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("riders.rider_id"),
        nullable=False,
        index=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False,
    )

    assigned_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )