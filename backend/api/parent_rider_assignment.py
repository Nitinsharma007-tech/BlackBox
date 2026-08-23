from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db

from backend.models.parent import Parent
from backend.models.rider import Rider
from backend.models.parent_rider_assignment import (
    ParentRiderAssignment,
)

from backend.schemas.parent_rider_assignment import (
    ParentRiderAssignmentCreate,
    ParentRiderAssignmentResponse,
)


router = APIRouter(
    prefix="/api/v1/parent-rider-assignments",
    tags=["Parent Rider Assignments"],
)


# ============================================================
# CREATE ASSIGNMENT
# ============================================================

@router.post(
    "",
    response_model=ParentRiderAssignmentResponse,
    status_code=201,
)
def create_assignment(
    assignment_data: ParentRiderAssignmentCreate,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Verify parent
    # --------------------------------------------------------

    parent = db.execute(
        select(Parent).where(
            Parent.parent_id
            == assignment_data.parent_id
        )
    ).scalar_one_or_none()

    if parent is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Parent "
                f"'{assignment_data.parent_id}' "
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
    # Check duplicate active relationship
    # --------------------------------------------------------

    existing_assignment = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.parent_id
            == assignment_data.parent_id,

            ParentRiderAssignment.rider_id
            == assignment_data.rider_id,

            ParentRiderAssignment.status
            == "active",
        )
    ).scalar_one_or_none()

    if existing_assignment is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "This parent is already actively "
                "assigned to this rider."
            ),
        )

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    assignment = ParentRiderAssignment(
        parent_id=assignment_data.parent_id,
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
# GET ALL
# ============================================================

@router.get(
    "",
    response_model=list[ParentRiderAssignmentResponse],
)
def get_assignments(
    db: Session = Depends(get_db),
):

    statement = (
        select(ParentRiderAssignment)
        .order_by(
            ParentRiderAssignment.assigned_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# GET PARENT ASSIGNMENTS
# ============================================================

@router.get(
    "/parent/{parent_id}",
    response_model=list[ParentRiderAssignmentResponse],
)
def get_parent_assignments(
    parent_id: str,
    db: Session = Depends(get_db),
):

    statement = (
        select(ParentRiderAssignment)
        .where(
            ParentRiderAssignment.parent_id
            == parent_id
        )
        .order_by(
            ParentRiderAssignment.assigned_at.desc()
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
    response_model=list[ParentRiderAssignmentResponse],
)
def get_rider_assignments(
    rider_id: str,
    db: Session = Depends(get_db),
):

    statement = (
        select(ParentRiderAssignment)
        .where(
            ParentRiderAssignment.rider_id
            == rider_id
        )
        .order_by(
            ParentRiderAssignment.assigned_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# GET SINGLE ASSIGNMENT
# ============================================================

@router.get(
    "/{assignment_id}",
    response_model=ParentRiderAssignmentResponse,
)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):

    assignment = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.id
            == assignment_id
        )
    ).scalar_one_or_none()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found.",
        )

    return assignment


# ============================================================
# REMOVE ASSIGNMENT
# ============================================================

@router.post(
    "/{assignment_id}/remove",
    response_model=ParentRiderAssignmentResponse,
)
def remove_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):

    assignment = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.id
            == assignment_id
        )
    ).scalar_one_or_none()

    if assignment is None:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found.",
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