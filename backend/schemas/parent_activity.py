from datetime import datetime

from pydantic import BaseModel


class ParentActivityItem(BaseModel):

    type: str

    severity: str

    title: str

    message: str

    rider_id: str | None = None

    rider_name: str | None = None

    vehicle_id: str | None = None

    alert_id: str | None = None

    incident_id: int | None = None

    status: str | None = None

    timestamp: datetime


class ParentActivityResponse(BaseModel):

    parent_id: str

    activities: list[ParentActivityItem]