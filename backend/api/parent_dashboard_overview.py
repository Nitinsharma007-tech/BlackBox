from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select, inspect
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
from backend.models.device import Device
from backend.models.telemetry import Telemetry
from backend.models.safety_event import SafetyEvent
from backend.models.emergency_alert import EmergencyAlert

from backend.services.tracking_service import (
    tracking_service,
)

from backend.services.safety_status_service import (
    safety_status_service,
)

from backend.schemas.parent_dashboard_overview import (
    ParentDashboardOverviewResponse,
)


router = APIRouter(
    prefix="/api/v1/parent-dashboard",
    tags=["Parent Dashboard Overview"],
)


# ============================================================
# SQLALCHEMY MODEL → DICTIONARY
# ============================================================

def model_to_dict(model):

    if model is None:
        return None

    return {
        column.key: getattr(model, column.key)
        for column in inspect(model).mapper.column_attrs
    }


# ============================================================
# PARENT DASHBOARD OVERVIEW
# ============================================================

@router.get(
    "/{parent_id}/overview",
    response_model=ParentDashboardOverviewResponse,
)
def get_parent_dashboard_overview(
    parent_id: str,
    db: Session = Depends(get_db),
):

    # ========================================================
    # 1. VERIFY PARENT
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

    parent_data = model_to_dict(parent)

    # ========================================================
    # 2. GET ACTIVE RIDERS
    # ========================================================

    assignments = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.parent_id == parent_id,
            ParentRiderAssignment.status == "active",
        )
    ).scalars().all()

    riders_data = []
    tracking_data = []
    activities = []

    # ========================================================
    # SUMMARY COUNTERS
    # ========================================================

    total_riders = 0
    online_riders = 0
    offline_riders = 0

    safe_riders = 0
    at_risk_riders = 0
    danger_riders = 0

    # ========================================================
    # 3. PROCESS RIDERS
    # ========================================================

    for assignment in assignments:

        rider = db.execute(
            select(Rider).where(
                Rider.rider_id == assignment.rider_id
            )
        ).scalar_one_or_none()

        if rider is None:
            continue

        total_riders += 1

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

        # ----------------------------------------------------
        # VEHICLE → DEVICE
        # ----------------------------------------------------

        device = None

        if vehicle:

            device_assignment = db.execute(
                select(DeviceVehicleAssignment).where(
                    DeviceVehicleAssignment.vehicle_id
                    == vehicle.vehicle_id,
                    DeviceVehicleAssignment.status == "active",
                )
            ).scalar_one_or_none()

            if device_assignment:

                device = db.execute(
                    select(Device).where(
                        Device.device_id
                        == device_assignment.device_id
                    )
                ).scalar_one_or_none()

        # ----------------------------------------------------
        # LATEST TELEMETRY
        # ----------------------------------------------------

        telemetry = None

        if device:

            telemetry = db.execute(
                select(Telemetry)
                .where(
                    Telemetry.device_id
                    == device.device_id
                )
                .order_by(
                    Telemetry.timestamp.desc()
                )
                .limit(1)
            ).scalar_one_or_none()

        # ----------------------------------------------------
        # INCIDENTS
        # ----------------------------------------------------

        incidents = []

        if device:

            incidents = db.execute(
                select(SafetyEvent)
                .where(
                    SafetyEvent.device_id
                    == device.device_id
                )
                .order_by(
                    SafetyEvent.timestamp.desc()
                )
                .limit(10)
            ).scalars().all()

        # ----------------------------------------------------
        # ALERTS
        # ----------------------------------------------------

        alerts = db.execute(
            select(EmergencyAlert)
            .where(
                EmergencyAlert.parent_id == parent_id,
                EmergencyAlert.rider_id == rider.rider_id,
            )
            .order_by(
                EmergencyAlert.created_at.desc()
            )
            .limit(10)
        ).scalars().all()

        # ----------------------------------------------------
        # SAFETY STATUS
        # ----------------------------------------------------

        safety = safety_status_service.calculate_status(
            device=device,
            latest_telemetry=telemetry,
            recent_incidents=incidents,
        )

        safety_status = safety["status"]

        # ----------------------------------------------------
        # ONLINE / OFFLINE
        # ----------------------------------------------------

        if (
            telemetry is not None
            and tracking_service.get_tracking_status(
                telemetry.timestamp
            ) == "online"
        ):
            online_riders += 1
        else:
            offline_riders += 1

        # ----------------------------------------------------
        # SAFETY COUNTERS
        # ----------------------------------------------------

        if safety_status == "safe":

            safe_riders += 1

        elif safety_status == "at_risk":

            at_risk_riders += 1

        elif safety_status == "danger":

            danger_riders += 1

        # ====================================================
        # RIDER DATA
        # ====================================================

        riders_data.append(
            {
                "rider": model_to_dict(rider),

                "vehicle": model_to_dict(vehicle),

                "device": model_to_dict(device),

                "latest_telemetry": (
                    model_to_dict(telemetry)
                ),

                "safety_status": safety,

                "recent_incidents": [
                    model_to_dict(incident)
                    for incident in incidents
                ],

                "alerts": [
                    model_to_dict(alert)
                    for alert in alerts
                ],
            }
        )

        # ====================================================
        # TRACKING DATA
        # ====================================================

        tracking_data.append(
            {
                "rider_id": rider.rider_id,

                "rider_name": rider.full_name,

                "vehicle_id": (
                    vehicle.vehicle_id
                    if vehicle
                    else None
                ),

                "registration_number": (
                    vehicle.registration_number
                    if vehicle
                    else None
                ),

                "device_id": (
                    device.device_id
                    if device
                    else None
                ),

                "latitude": (
                    telemetry.latitude
                    if telemetry
                    else None
                ),

                "longitude": (
                    telemetry.longitude
                    if telemetry
                    else None
                ),

                "speed": (
                    telemetry.speed
                    if telemetry
                    else None
                ),

                "timestamp": (
                    telemetry.timestamp
                    if telemetry
                    else None
                ),

                "status": (
                    tracking_service.get_tracking_status(
                        telemetry.timestamp
                    )
                    if telemetry
                    else "offline"
                ),
            }
        )

        # ====================================================
        # ACTIVITY — INCIDENTS
        # ====================================================

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

                    "vehicle_id": (
                        vehicle.vehicle_id
                        if vehicle
                        else None
                    ),

                    "alert_id": None,

                    "incident_id": incident.id,

                    "status": incident.status,

                    "timestamp": incident.timestamp,
                }
            )

        # ====================================================
        # ACTIVITY — ALERTS
        # ====================================================

        for alert in alerts:

            activities.append(
                {
                    "type": "emergency_alert",

                    "severity": alert.severity,

                    "title": "Safety Alert",

                    "message": alert.message,

                    "rider_id": rider.rider_id,

                    "rider_name": rider.full_name,

                    "vehicle_id": (
                        vehicle.vehicle_id
                        if vehicle
                        else None
                    ),

                    "alert_id": alert.alert_id,

                    "incident_id": alert.incident_id,

                    "status": alert.status,

                    "timestamp": alert.created_at,
                }
            )

    # ========================================================
    # SORT ACTIVITY
    # ========================================================

    activities.sort(
        key=lambda item: item["timestamp"],
        reverse=True,
    )

    activities = activities[:20]

    # ========================================================
    # PENDING ALERTS
    # ========================================================

    pending_alerts = db.execute(
        select(EmergencyAlert).where(
            EmergencyAlert.parent_id == parent_id,
            EmergencyAlert.status == "pending",
        )
    ).scalars().all()

    # ========================================================
    # RECENT INCIDENT COUNT
    # ========================================================

    recent_incident_count = 0

    for rider_data in riders_data:

        recent_incident_count += len(
            rider_data["recent_incidents"]
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = {
        "total_riders": total_riders,

        "online_riders": online_riders,

        "offline_riders": offline_riders,

        "safe_riders": safe_riders,

        "at_risk_riders": at_risk_riders,

        "danger_riders": danger_riders,

        "pending_alerts": len(
            pending_alerts
        ),

        "recent_incidents": recent_incident_count,
    }

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "parent": parent_data,

        "summary": summary,

        "riders": riders_data,

        "tracking": tracking_data,

        "activities": activities,
    }