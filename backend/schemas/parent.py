from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParentCreate(BaseModel):

    parent_id: str

    full_name: str

    phone: str

    email: str | None = None


class ParentResponse(BaseModel):

    id: int

    parent_id: str

    full_name: str

    phone: str

    email: str | None

    is_active: bool

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )