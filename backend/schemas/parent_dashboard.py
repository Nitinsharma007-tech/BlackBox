from typing import Any

from pydantic import BaseModel


class ParentDashboardResponse(BaseModel):

    parent: dict[str, Any]

    riders: list[dict[str, Any]]