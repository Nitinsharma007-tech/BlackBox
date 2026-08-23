from pydantic import BaseModel


class ParentDashboardSummaryResponse(BaseModel):

    parent_id: str

    total_riders: int

    online_riders: int

    offline_riders: int

    safe_riders: int

    at_risk_riders: int

    danger_riders: int

    pending_alerts: int

    recent_incidents: int