from datetime import datetime

from pydantic import BaseModel


class TrackingResponse(BaseModel):

    rider_id: str

    vehicle_id: str | None = None

    device_id: str | None = None

    latitude: float | None = None

    longitude: float | None = None

    speed: float | None = None

    timestamp: datetime | None = None

    status: str