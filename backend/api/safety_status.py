from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select

from sqlalchemy.orm import Session

from backend.database.postgresql import get_db

from backend.models.device import Device

from backend.models.rider import Rider

from backend.models.vehicle import Vehicle

from backend.models.vehicle_rider_assignment import (
    VehicleRiderAssignment,
)

from backend.models.device_vehicle_assignment import (
    DeviceVehicleAssignment,
)

from backend.models.telemetry import Telemetry

from backend.models.safety_event import SafetyEvent

from backend.schemas.safety_status import (
    SafetyStatusResponse,
)

from backend.services.safety_status_service import (
    safety_status_service,
)


router = APIRouter(
    prefix="/api/v1/safety-status",
    tags=["Safety Status"],
)


# ============================================================
# DEVICE SAFETY STATUS
# ============================================================

@router.get(
    "/device/{device_id}",
    response_model=SafetyStatusResponse,
)
def get_device_safety_status(
    device_id: str,
    db: Session = Depends(get_db),
):

    # ========================================================
    # DEVICE
    # ========================================================

    device = db.execute(
        select(Device).where(
            Device.device_id == device_id
        )
    ).scalar_one_or_none()

    if device is None:

        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found.",
        )

    # ========================================================
    # LATEST TELEMETRY
    # ========================================================

    latest_telemetry = db.execute(
        select(Telemetry)
        .where(
            Telemetry.device_id == device_id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(1)
    ).scalar_one_or_none()

    # ========================================================
    # RECENT INCIDENTS
    # ========================================================

    recent_incidents = db.execute(
        select(SafetyEvent)
        .where(
            SafetyEvent.device_id == device_id
        )
        .order_by(
            SafetyEvent.timestamp.desc()
        )
        .limit(10)
    ).scalars().all()

    # ========================================================
    # VEHICLE
    # ========================================================

    device_assignment = db.execute(
        select(DeviceVehicleAssignment).where(
            DeviceVehicleAssignment.device_id
            == device_id,
            DeviceVehicleAssignment.status
            == "active",
        )
    ).scalar_one_or_none()

    vehicle = None

    if device_assignment:

        vehicle = db.execute(
            select(Vehicle).where(
                Vehicle.vehicle_id
                == device_assignment.vehicle_id
            )
        ).scalar_one_or_none()

    # ========================================================
    # RIDER
    # ========================================================

    rider = None

    if vehicle:

        rider_assignment = db.execute(
            select(VehicleRiderAssignment).where(
                VehicleRiderAssignment.vehicle_id
                == vehicle.vehicle_id,
                VehicleRiderAssignment.status
                == "active",
            )
        ).scalar_one_or_none()

        if rider_assignment:

            rider = db.execute(
                select(Rider).where(
                    Rider.rider_id
                    == rider_assignment.rider_id
                )
            ).scalar_one_or_none()

    # ========================================================
    # CALCULATE SAFETY
    # ========================================================

    safety = (
        safety_status_service.calculate_status(
            device=device,
            latest_telemetry=latest_telemetry,
            recent_incidents=recent_incidents,
        )
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "device_id": device_id,

        "rider_id": (
            rider.rider_id
            if rider
            else None
        ),

        "vehicle_id": (
            vehicle.vehicle_id
            if vehicle
            else None
        ),

        "status": safety["status"],

        "severity": safety["severity"],

        "reason": safety["reason"],

        "speed": (
            latest_telemetry.speed
            if latest_telemetry
            else None
        ),

        "latitude": (
            latest_telemetry.latitude
            if latest_telemetry
            else None
        ),

        "longitude": (
            latest_telemetry.longitude
            if latest_telemetry
            else None
        ),

        "last_seen": (
            latest_telemetry.timestamp
            if latest_telemetry
            else None
        ),
    }