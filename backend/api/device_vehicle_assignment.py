from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db
from backend.models.device import Device
from backend.models.vehicle import Vehicle
from backend.models.device_vehicle_assignment import (
    DeviceVehicleAssignment,
)
from backend.schemas.device_vehicle_assignment import (
    DeviceVehicleAssignmentCreate,
    DeviceVehicleAssignmentResponse,
)


router = APIRouter(
    prefix="/api/v1/device-vehicle-assignments",
    tags=["Device Vehicle Assignments"],
)


# ============================================================
# CREATE ASSIGNMENT
# ============================================================

@router.post(
    "",
    response_model=DeviceVehicleAssignmentResponse,
    status_code=201,
)
def create_assignment(
    assignment_data: DeviceVehicleAssignmentCreate,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # 1. Verify device exists
    # --------------------------------------------------------

    device = db.execute(
        select(Device).where(
            Device.device_id
            == assignment_data.device_id
        )
    ).scalar_one_or_none()

    if device is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Device "
                f"'{assignment_data.device_id}' "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # 2. Verify vehicle exists
    # --------------------------------------------------------

    vehicle = db.execute(
        select(Vehicle).where(
            Vehicle.vehicle_id
            == assignment_data.vehicle_id
        )
    ).scalar_one_or_none()

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Vehicle "
                f"'{assignment_data.vehicle_id}' "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # 3. Check whether device is already assigned
    # --------------------------------------------------------

    active_device_assignment = db.execute(
        select(DeviceVehicleAssignment).where(
            DeviceVehicleAssignment.device_id
            == assignment_data.device_id,
            DeviceVehicleAssignment.status
            == "active",
        )
    ).scalar_one_or_none()

    if active_device_assignment is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Device "
                f"'{assignment_data.device_id}' "
                "is already assigned to "
                f"vehicle "
                f"'{active_device_assignment.vehicle_id}'."
            ),
        )

    # --------------------------------------------------------
    # 4. Check whether vehicle already has a device
    # --------------------------------------------------------

    active_vehicle_assignment = db.execute(
        select(DeviceVehicleAssignment).where(
            DeviceVehicleAssignment.vehicle_id
            == assignment_data.vehicle_id,
            DeviceVehicleAssignment.status
            == "active",
        )
    ).scalar_one_or_none()

    if active_vehicle_assignment is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Vehicle "
                f"'{assignment_data.vehicle_id}' "
                "already has an active device "
                f"'{active_vehicle_assignment.device_id}'."
            ),
        )

    # --------------------------------------------------------
    # 5. Create assignment
    # --------------------------------------------------------

    assignment = DeviceVehicleAssignment(
        device_id=assignment_data.device_id,
        vehicle_id=assignment_data.vehicle_id,
        installed_at=datetime.now(timezone.utc),
        status="active",
        installed_by=assignment_data.installed_by,
    )

    db.add(assignment)

    try:
        db.commit()
        db.refresh(assignment)

    except Exception:
        db.rollback()
        raise

    return assignment


# ============================================================
# GET ALL ASSIGNMENTS
# ============================================================

@router.get(
    "",
    response_model=list[DeviceVehicleAssignmentResponse],
)
def get_assignments(
    db: Session = Depends(get_db),
):
    statement = (
        select(DeviceVehicleAssignment)
        .order_by(
            DeviceVehicleAssignment.installed_at.desc()
        )
    )

    assignments = (
        db.execute(statement)
        .scalars()
        .all()
    )

    return assignments


# ============================================================
# GET ASSIGNMENT BY ID
# ============================================================

@router.get(
    "/{assignment_id}",
    response_model=DeviceVehicleAssignmentResponse,
)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):
    assignment = db.execute(
        select(DeviceVehicleAssignment).where(
            DeviceVehicleAssignment.id
            == assignment_id
        )
    ).scalar_one_or_none()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Assignment "
                f"'{assignment_id}' "
                "not found."
            ),
        )

    return assignment


# ============================================================
# GET DEVICE ASSIGNMENTS
# ============================================================

@router.get(
    "/device/{device_id}",
    response_model=list[DeviceVehicleAssignmentResponse],
)
def get_device_assignments(
    device_id: str,
    db: Session = Depends(get_db),
):
    statement = (
        select(DeviceVehicleAssignment)
        .where(
            DeviceVehicleAssignment.device_id
            == device_id
        )
        .order_by(
            DeviceVehicleAssignment.installed_at.desc()
        )
    )

    assignments = (
        db.execute(statement)
        .scalars()
        .all()
    )

    return assignments


# ============================================================
# GET VEHICLE ASSIGNMENTS
# ============================================================

@router.get(
    "/vehicle/{vehicle_id}",
    response_model=list[DeviceVehicleAssignmentResponse],
)
def get_vehicle_assignments(
    vehicle_id: str,
    db: Session = Depends(get_db),
):
    statement = (
        select(DeviceVehicleAssignment)
        .where(
            DeviceVehicleAssignment.vehicle_id
            == vehicle_id
        )
        .order_by(
            DeviceVehicleAssignment.installed_at.desc()
        )
    )

    assignments = (
        db.execute(statement)
        .scalars()
        .all()
    )

    return assignments


# ============================================================
# REMOVE DEVICE FROM VEHICLE
# ============================================================

@router.post(
    "/{assignment_id}/remove",
    response_model=DeviceVehicleAssignmentResponse,
)
def remove_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):
    assignment = db.execute(
        select(DeviceVehicleAssignment).where(
            DeviceVehicleAssignment.id
            == assignment_id
        )
    ).scalar_one_or_none()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Assignment "
                f"'{assignment_id}' "
                "not found."
            ),
        )

    if assignment.status != "active":
        raise HTTPException(
            status_code=409,
            detail=(
                "This device-vehicle assignment "
                "is already inactive."
            ),
        )

    assignment.status = "removed"
    assignment.removed_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(assignment)

    except Exception:
        db.rollback()
        raise

    return assignment