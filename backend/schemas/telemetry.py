from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TelemetryCreate(BaseModel):
    device_id: str
    timestamp: datetime

    latitude: float | None = None
    longitude: float | None = None
    speed: float | None = None

    acceleration_x: float | None = None
    acceleration_y: float | None = None
    acceleration_z: float | None = None

    gyro_x: float | None = None
    gyro_y: float | None = None
    gyro_z: float | None = None

    roll: float | None = None
    pitch: float | None = None


class TelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    timestamp: datetime

    latitude: float | None = None
    longitude: float | None = None
    speed: float | None = None

    acceleration_x: float | None = None
    acceleration_y: float | None = None
    acceleration_z: float | None = None

    gyro_x: float | None = None
    gyro_y: float | None = None
    gyro_z: float | None = None

    roll: float | None = None
    pitch: float | None = None