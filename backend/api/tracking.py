from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db

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

from backend.schemas.tracking import TrackingResponse

from backend.services.tracking_service import (
    tracking_service,
)


router = APIRouter(
    prefix="/api/v1/tracking",
    tags=["Live Tracking"],
)


# ============================================================
# RIDER LIVE LOCATION
# ============================================================

@router.get(
    "/rider/{rider_id}",
    response_model=TrackingResponse,
)
def get_rider_tracking(
    rider_id: str,
    db: Session = Depends(get_db),
):

    # ========================================================
    # 1. RIDER
    # ========================================================

    rider = db.execute(
        select(Rider).where(
            Rider.rider_id == rider_id
        )
    ).scalar_one_or_none()

    if rider is None:
        raise HTTPException(
            status_code=404,
            detail=f"Rider '{rider_id}' not found.",
        )

    # ========================================================
    # 2. RIDER → VEHICLE
    # ========================================================

    vehicle_assignment = db.execute(
        select(VehicleRiderAssignment).where(
            VehicleRiderAssignment.rider_id == rider_id,
            VehicleRiderAssignment.status == "active",
        )
    ).scalar_one_or_none()

    if vehicle_assignment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No active vehicle assigned "
                f"to rider '{rider_id}'."
            ),
        )

    vehicle = db.execute(
        select(Vehicle).where(
            Vehicle.vehicle_id
            == vehicle_assignment.vehicle_id
        )
    ).scalar_one_or_none()

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Assigned vehicle not found.",
        )

    # ========================================================
    # 3. VEHICLE → DEVICE
    # ========================================================

    device_assignment = db.execute(
        select(DeviceVehicleAssignment).where(
            DeviceVehicleAssignment.vehicle_id
            == vehicle.vehicle_id,
            DeviceVehicleAssignment.status
            == "active",
        )
    ).scalar_one_or_none()

    if device_assignment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No active device assigned "
                f"to vehicle '{vehicle.vehicle_id}'."
            ),
        )

    device = db.execute(
        select(Device).where(
            Device.device_id
            == device_assignment.device_id
        )
    ).scalar_one_or_none()

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Assigned device not found.",
        )

    # ========================================================
    # 4. LATEST TELEMETRY
    # ========================================================

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

    if telemetry is None:
        return {
            "rider_id": rider_id,
            "vehicle_id": vehicle.vehicle_id,
            "device_id": device.device_id,
            "latitude": None,
            "longitude": None,
            "speed": None,
            "timestamp": None,
            "status": "offline",
        }

    # ========================================================
    # 5. CALCULATE ONLINE / OFFLINE
    # ========================================================

    status = (
        tracking_service.get_tracking_status(
            telemetry.timestamp
        )
    )

    # ========================================================
    # 6. RETURN LIVE LOCATION
    # ========================================================

    return {
        "rider_id": rider_id,
        "vehicle_id": vehicle.vehicle_id,
        "device_id": device.device_id,
        "latitude": telemetry.latitude,
        "longitude": telemetry.longitude,
        "speed": telemetry.speed,
        "timestamp": telemetry.timestamp,
        "status": status,
    }