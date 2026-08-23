from typing import Optional

from datetime import datetime

from pydantic import BaseModel


class SafetyStatusResponse(BaseModel):

    device_id: str

    rider_id: Optional[str] = None

    vehicle_id: Optional[str] = None

    status: str

    severity: str

    reason: str

    speed: Optional[float] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    last_seen: Optional[datetime] = None