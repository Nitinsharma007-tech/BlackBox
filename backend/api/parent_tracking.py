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

from backend.schemas.parent_tracking import (
    ParentTrackingResponse,
)

from backend.services.tracking_service import (
    tracking_service,
)


router = APIRouter(
    prefix="/api/v1/parent-tracking",
    tags=["Parent Live Tracking"],
)


# ============================================================
# PARENT LIVE TRACKING
# ============================================================

@router.get(
    "/{parent_id}",
    response_model=ParentTrackingResponse,
)
def get_parent_tracking(
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
    # 2. GET ACTIVE RIDER ASSIGNMENTS
    # ========================================================

    assignments = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.parent_id == parent_id,
            ParentRiderAssignment.status == "active",
        )
    ).scalars().all()

    riders = []

    # ========================================================
    # 3. BUILD TRACKING DATA
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
        # DEFAULT OFFLINE
        # ----------------------------------------------------

        status = "offline"

        if telemetry:

            status = (
                tracking_service.get_tracking_status(
                    telemetry.timestamp
                )
            )

        # ----------------------------------------------------
        # ADD RIDER
        # ----------------------------------------------------

        riders.append(
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

                "status": status,
            }
        )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "parent_id": parent_id,
        "riders": riders,
    }