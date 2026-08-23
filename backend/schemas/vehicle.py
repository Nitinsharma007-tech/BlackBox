from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VehicleCreate(BaseModel):

    vehicle_id: str

    registration_number: str

    make: str | None = None

    model: str | None = None

    year: int | None = None


class VehicleResponse(BaseModel):

    id: int

    vehicle_id: str

    registration_number: str

    make: str | None = None

    model: str | None = None

    year: int | None = None

    is_active: bool

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )