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
from backend.models.device import Device
from backend.models.telemetry import Telemetry
from backend.models.safety_event import SafetyEvent
from backend.models.emergency_alert import EmergencyAlert

from backend.services.safety_status_service import (
    safety_status_service,
)

from backend.schemas.parent_dashboard_summary import (
    ParentDashboardSummaryResponse,
)


router = APIRouter(
    prefix="/api/v1/parent-dashboard",
    tags=["Parent Dashboard Summary"],
)


# ============================================================
# PARENT DASHBOARD SUMMARY
# ============================================================

@router.get(
    "/{parent_id}/summary",
    response_model=ParentDashboardSummaryResponse,
)
def get_parent_dashboard_summary(
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

    # ========================================================
    # 2. GET ACTIVE RIDERS
    # ========================================================

    assignments = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.parent_id == parent_id,
            ParentRiderAssignment.status == "active",
        )
    ).scalars().all()

    # ========================================================
    # COUNTERS
    # ========================================================

    total_riders = 0
    online_riders = 0
    offline_riders = 0

    safe_riders = 0
    at_risk_riders = 0
    danger_riders = 0

    # ========================================================
    # 3. PROCESS EACH RIDER
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
        # RECENT INCIDENTS
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
        # CALCULATE SAFETY
        # ----------------------------------------------------

        safety = (
            safety_status_service.calculate_status(
                device=device,
                latest_telemetry=telemetry,
                recent_incidents=incidents,
            )
        )

        status = safety["status"]

        # ----------------------------------------------------
        # ONLINE / OFFLINE
        # ----------------------------------------------------

        if status == "offline":

            offline_riders += 1

        else:

            online_riders += 1

        # ----------------------------------------------------
        # SAFETY STATE
        # ----------------------------------------------------

        if status == "safe":

            safe_riders += 1

        elif status == "at_risk":

            at_risk_riders += 1

        elif status == "danger":

            danger_riders += 1

    # ========================================================
    # 4. PENDING ALERTS
    # ========================================================

    pending_alerts = db.execute(
        select(EmergencyAlert).where(
            EmergencyAlert.parent_id == parent_id,
            EmergencyAlert.status == "pending",
        )
    ).scalars().all()

    # ========================================================
    # 5. RECENT INCIDENTS
    # ========================================================

    recent_incidents = 0

    for assignment in assignments:

        rider = db.execute(
            select(Rider).where(
                Rider.rider_id == assignment.rider_id
            )
        ).scalar_one_or_none()

        if rider is None:
            continue

        vehicle_assignment = db.execute(
            select(VehicleRiderAssignment).where(
                VehicleRiderAssignment.rider_id
                == rider.rider_id,
                VehicleRiderAssignment.status == "active",
            )
        ).scalar_one_or_none()

        if vehicle_assignment is None:
            continue

        device_assignment = db.execute(
            select(DeviceVehicleAssignment).where(
                DeviceVehicleAssignment.vehicle_id
                == vehicle_assignment.vehicle_id,
                DeviceVehicleAssignment.status == "active",
            )
        ).scalar_one_or_none()

        if device_assignment is None:
            continue

        incidents_count = db.execute(
            select(SafetyEvent).where(
                SafetyEvent.device_id
                == device_assignment.device_id
            )
        ).scalars().all()

        recent_incidents += len(
            incidents_count
        )

    # ========================================================
    # 6. RESPONSE
    # ========================================================

    return {
        "parent_id": parent_id,

        "total_riders": total_riders,

        "online_riders": online_riders,

        "offline_riders": offline_riders,

        "safe_riders": safe_riders,

        "at_risk_riders": at_risk_riders,

        "danger_riders": danger_riders,

        "pending_alerts": len(
            pending_alerts
        ),

        "recent_incidents": recent_incidents,
    }