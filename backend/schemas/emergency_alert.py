from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EmergencyAlertCreate(BaseModel):

    alert_id: str

    parent_id: str

    rider_id: str

    vehicle_id: str | None = None

    device_id: str | None = None

    incident_id: int | None = None

    alert_type: str

    severity: str

    message: str


class EmergencyAlertResponse(BaseModel):

    id: int

    alert_id: str

    parent_id: str

    rider_id: str

    vehicle_id: str | None

    device_id: str | None

    incident_id: int | None

    alert_type: str

    severity: str

    message: str

    status: str

    created_at: datetime

    acknowledged_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )