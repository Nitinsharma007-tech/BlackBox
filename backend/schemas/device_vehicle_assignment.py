from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ============================================================
# CREATE ASSIGNMENT
# ============================================================

class DeviceVehicleAssignmentCreate(BaseModel):

    device_id: str

    vehicle_id: str

    installed_by: str | None = None


# ============================================================
# ASSIGNMENT RESPONSE
# ============================================================

class DeviceVehicleAssignmentResponse(BaseModel):

    id: int

    device_id: str

    vehicle_id: str

    installed_at: datetime

    removed_at: datetime | None

    status: str

    installed_by: str | None

    model_config = ConfigDict(
        from_attributes=True
    )