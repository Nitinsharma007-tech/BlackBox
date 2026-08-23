from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db
from backend.models.vehicle import Vehicle
from backend.models.rider import Rider
from backend.models.vehicle_rider_assignment import (
    VehicleRiderAssignment,
)
from backend.schemas.vehicle_rider_assignment import (
    VehicleRiderAssignmentCreate,
    VehicleRiderAssignmentResponse,
)


router = APIRouter(
    prefix="/api/v1/vehicle-rider-assignments",
    tags=["Vehicle Rider Assignments"],
)


# ============================================================
# CREATE ASSIGNMENT
# ============================================================

@router.post(
    "",
    response_model=VehicleRiderAssignmentResponse,
    status_code=201,
)
def create_assignment(
    assignment_data: VehicleRiderAssignmentCreate,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Verify vehicle
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
    # Verify rider
    # --------------------------------------------------------

    rider = db.execute(
        select(Rider).where(
            Rider.rider_id
            == assignment_data.rider_id
        )
    ).scalar_one_or_none()

    if rider is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Rider "
                f"'{assignment_data.rider_id}' "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # Check active vehicle assignment
    # --------------------------------------------------------

    active_vehicle_assignment = db.execute(
        select(VehicleRiderAssignment).where(
            VehicleRiderAssignment.vehicle_id
            == assignment_data.vehicle_id,
            VehicleRiderAssignment.status
            == "active",
        )
    ).scalar_one_or_none()

    if active_vehicle_assignment is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Vehicle "
                f"'{assignment_data.vehicle_id}' "
                "already has an active rider "
                f"'{active_vehicle_assignment.rider_id}'."
            ),
        )

    # --------------------------------------------------------
    # Check active rider assignment
    # --------------------------------------------------------

    active_rider_assignment = db.execute(
        select(VehicleRiderAssignment).where(
            VehicleRiderAssignment.rider_id
            == assignment_data.rider_id,
            VehicleRiderAssignment.status
            == "active",
        )
    ).scalar_one_or_none()

    if active_rider_assignment is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Rider "
                f"'{assignment_data.rider_id}' "
                "is already assigned to vehicle "
                f"'{active_rider_assignment.vehicle_id}'."
            ),
        )

    # --------------------------------------------------------
    # Create assignment
    # --------------------------------------------------------

    assignment = VehicleRiderAssignment(
        vehicle_id=assignment_data.vehicle_id,
        rider_id=assignment_data.rider_id,
        assigned_at=datetime.now(timezone.utc),
        status="active",
        assigned_by=assignment_data.assigned_by,
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
    response_model=list[VehicleRiderAssignmentResponse],
)
def get_assignments(
    db: Session = Depends(get_db),
):

    statement = (
        select(VehicleRiderAssignment)
        .order_by(
            VehicleRiderAssignment.assigned_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# GET ASSIGNMENT
# ============================================================

@router.get(
    "/{assignment_id}",
    response_model=VehicleRiderAssignmentResponse,
)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):

    assignment = db.execute(
        select(VehicleRiderAssignment).where(
            VehicleRiderAssignment.id
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
# GET VEHICLE ASSIGNMENTS
# ============================================================

@router.get(
    "/vehicle/{vehicle_id}",
    response_model=list[VehicleRiderAssignmentResponse],
)
def get_vehicle_assignments(
    vehicle_id: str,
    db: Session = Depends(get_db),
):

    statement = (
        select(VehicleRiderAssignment)
        .where(
            VehicleRiderAssignment.vehicle_id
            == vehicle_id
        )
        .order_by(
            VehicleRiderAssignment.assigned_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# GET RIDER ASSIGNMENTS
# ============================================================

@router.get(
    "/rider/{rider_id}",
    response_model=list[VehicleRiderAssignmentResponse],
)
def get_rider_assignments(
    rider_id: str,
    db: Session = Depends(get_db),
):

    statement = (
        select(VehicleRiderAssignment)
        .where(
            VehicleRiderAssignment.rider_id
            == rider_id
        )
        .order_by(
            VehicleRiderAssignment.assigned_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# REMOVE ASSIGNMENT
# ============================================================

@router.post(
    "/{assignment_id}/remove",
    response_model=VehicleRiderAssignmentResponse,
)
def remove_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):

    assignment = db.execute(
        select(VehicleRiderAssignment).where(
            VehicleRiderAssignment.id
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
            detail="Assignment is already inactive.",
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