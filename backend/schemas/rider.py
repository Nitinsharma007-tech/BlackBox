from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiderCreate(BaseModel):

    rider_id: str

    full_name: str

    phone: str

    email: str | None = None

    emergency_contact_name: str | None = None

    emergency_contact_phone: str | None = None


class RiderResponse(BaseModel):

    id: int

    rider_id: str

    full_name: str

    phone: str

    email: str | None

    emergency_contact_name: str | None

    emergency_contact_phone: str | None

    is_active: bool

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )