from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VehicleRiderAssignmentCreate(BaseModel):

    vehicle_id: str

    rider_id: str

    assigned_by: str | None = None


class VehicleRiderAssignmentResponse(BaseModel):

    id: int

    vehicle_id: str

    rider_id: str

    assigned_at: datetime

    removed_at: datetime | None

    status: str

    assigned_by: str | None

    model_config = ConfigDict(
        from_attributes=True
    )