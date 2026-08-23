from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db

from backend.models.parent import Parent
from backend.models.parent_rider_assignment import (
    ParentRiderAssignment,
)
from backend.models.rider import Rider
from backend.models.vehicle_rider_assignment import (
    VehicleRiderAssignment,
)
from backend.models.vehicle import Vehicle
from backend.models.device_vehicle_assignment import (
    DeviceVehicleAssignment,
)
from backend.models.safety_event import SafetyEvent
from backend.models.emergency_alert import EmergencyAlert

from backend.schemas.parent_activity import (
    ParentActivityResponse,
)


router = APIRouter(
    prefix="/api/v1/parent-dashboard",
    tags=["Parent Activity"],
)


# ============================================================
# PARENT ACTIVITY FEED
# ============================================================

@router.get(
    "/{parent_id}/activity",
    response_model=ParentActivityResponse,
)
def get_parent_activity(
    parent_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):

    # ========================================================
    # VALIDATE LIMIT
    # ========================================================

    if limit < 1 or limit > 100:

        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100.",
        )

    # ========================================================
    # VERIFY PARENT
    # ========================================================

    parent = db.execute(
        select(Parent).where(
            Parent.parent_id == parent_id
        )
    ).scalar_one_or_none()

    if parent is None:

        raise HTTPException(
            status_code=404,
            detail=f"Parent '{parent_id}' not found.",
        )

    # ========================================================
    # GET ACTIVE PARENT → RIDER ASSIGNMENTS
    # ========================================================

    assignments = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.parent_id == parent_id,
            ParentRiderAssignment.status == "active",
        )
    ).scalars().all()

    activities = []

    # ========================================================
    # PROCESS RIDERS
    # ========================================================

    for assignment in assignments:

        rider = db.execute(
            select(Rider).where(
                Rider.rider_id == assignment.rider_id
            )
        ).scalar_one_or_none()

        if rider is None:
            continue

        # ----------------------------------------------------
        # RIDER → VEHICLE
        # ----------------------------------------------------

        vehicle_assignment = db.execute(
            select(VehicleRiderAssignment).where(
                VehicleRiderAssignment.rider_id
                == rider.rider_id,
                VehicleRiderAssignment.status == "active",
            )
        ).scalar_one_or_none()

        vehicle = None

        if vehicle_assignment:

            vehicle = db.execute(
                select(Vehicle).where(
                    Vehicle.vehicle_id
                    == vehicle_assignment.vehicle_id
                )
            ).scalar_one_or_none()

        vehicle_id = (
            vehicle.vehicle_id
            if vehicle
            else None
        )

        # ----------------------------------------------------
        # VEHICLE → DEVICE
        # ----------------------------------------------------

        device_id = None

        if vehicle:

            device_assignment = db.execute(
                select(DeviceVehicleAssignment).where(
                    DeviceVehicleAssignment.vehicle_id
                    == vehicle.vehicle_id,
                    DeviceVehicleAssignment.status
                    == "active",
                )
            ).scalar_one_or_none()

            if device_assignment:

                device_id = (
                    device_assignment.device_id
                )

        # ----------------------------------------------------
        # SAFETY EVENTS
        # ----------------------------------------------------

        if device_id:

            incidents = db.execute(
                select(SafetyEvent).where(
                    SafetyEvent.device_id
                    == device_id
                )
                .order_by(
                    SafetyEvent.timestamp.desc()
                )
                .limit(limit)
            ).scalars().all()

            for incident in incidents:

                activities.append(
                    {
                        "type": "safety_event",

                        "severity": incident.severity,

                        "title": (
                            incident.event_type
                            .replace("_", " ")
                            .title()
                            + " Detected"
                        ),

                        "message": incident.message,

                        "rider_id": rider.rider_id,

                        "rider_name": rider.full_name,

                        "vehicle_id": vehicle_id,

                        "alert_id": None,

                        "incident_id": incident.id,

                        "status": incident.status,

                        "timestamp": incident.timestamp,
                    }
                )

        # ----------------------------------------------------
        # EMERGENCY ALERTS
        # ----------------------------------------------------

        alerts = db.execute(
            select(EmergencyAlert).where(
                EmergencyAlert.parent_id == parent_id,
                EmergencyAlert.rider_id == rider.rider_id,
            )
            .order_by(
                EmergencyAlert.created_at.desc()
            )
            .limit(limit)
        ).scalars().all()

        for alert in alerts:

            activities.append(
                {
                    "type": "emergency_alert",

                    "severity": alert.severity,

                    "title": "Safety Alert",

                    "message": alert.message,

                    "rider_id": rider.rider_id,

                    "rider_name": rider.full_name,

                    "vehicle_id": vehicle_id,

                    "alert_id": alert.alert_id,

                    "incident_id": alert.incident_id,

                    "status": alert.status,

                    "timestamp": alert.created_at,
                }
            )

    # ========================================================
    # SORT CHRONOLOGICALLY
    # ========================================================

    activities.sort(
        key=lambda item: item["timestamp"],
        reverse=True,
    )

    # ========================================================
    # APPLY FINAL LIMIT
    # ========================================================

    activities = activities[:limit]

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "parent_id": parent_id,
        "activities": activities,
    }