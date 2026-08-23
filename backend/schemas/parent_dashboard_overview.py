from typing import Any

from pydantic import BaseModel


class ParentDashboardOverviewResponse(BaseModel):

    parent: dict[str, Any]

    summary: dict[str, Any]

    riders: list[dict[str, Any]]

    tracking: list[dict[str, Any]]

    activities: list[dict[str, Any]]