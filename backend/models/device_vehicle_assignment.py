from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgresql import Base


class DeviceVehicleAssignment(Base):
    __tablename__ = "device_vehicle_assignments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    device_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("devices.device_id"),
        nullable=False,
        index=True,
    )

    vehicle_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("vehicles.vehicle_id"),
        nullable=False,
        index=True,
    )

    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
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

    installed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )