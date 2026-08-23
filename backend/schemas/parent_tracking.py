from datetime import datetime

from pydantic import BaseModel


class ParentTrackingRiderResponse(BaseModel):

    rider_id: str

    rider_name: str

    vehicle_id: str | None = None

    registration_number: str | None = None

    device_id: str | None = None

    latitude: float | None = None

    longitude: float | None = None

    speed: float | None = None

    timestamp: datetime | None = None

    status: str


class ParentTrackingResponse(BaseModel):

    parent_id: str

    riders: list[ParentTrackingRiderResponse]