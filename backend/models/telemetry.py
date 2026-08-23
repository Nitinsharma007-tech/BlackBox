from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.postgresql import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    device_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    speed: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    acceleration_x: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    acceleration_y: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    acceleration_z: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    gyro_x: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    gyro_y: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    gyro_z: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    roll: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    pitch: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )