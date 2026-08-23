from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SafetyEventResponse(BaseModel):

    id: int

    device_id: str

    event_type: str

    severity: str

    message: str

    timestamp: datetime

    latitude: float | None = None

    longitude: float | None = None

    speed: float | None = None

    black_box_frozen: bool

    frozen_evidence_count: int
    status: str
    
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )