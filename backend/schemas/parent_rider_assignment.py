from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParentRiderAssignmentCreate(BaseModel):

    parent_id: str

    rider_id: str

    assigned_by: str | None = None


class ParentRiderAssignmentResponse(BaseModel):

    id: int

    parent_id: str

    rider_id: str

    assigned_at: datetime

    removed_at: datetime | None

    status: str

    assigned_by: str | None

    model_config = ConfigDict(
        from_attributes=True
    )