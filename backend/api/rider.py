from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db
from backend.models.rider import Rider
from backend.schemas.rider import (
    RiderCreate,
    RiderResponse,
)


router = APIRouter(
    prefix="/api/v1/riders",
    tags=["Riders"],
)


# ============================================================
# CREATE RIDER
# ============================================================

@router.post(
    "",
    response_model=RiderResponse,
    status_code=201,
)
def create_rider(
    rider_data: RiderCreate,
    db: Session = Depends(get_db),
):

    existing_rider = db.execute(
        select(Rider).where(
            Rider.rider_id == rider_data.rider_id
        )
    ).scalar_one_or_none()

    if existing_rider is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Rider "
                f"'{rider_data.rider_id}' "
                "already exists."
            ),
        )

    rider = Rider(
        rider_id=rider_data.rider_id,
        full_name=rider_data.full_name,
        phone=rider_data.phone,
        email=rider_data.email,
        emergency_contact_name=(
            rider_data.emergency_contact_name
        ),
        emergency_contact_phone=(
            rider_data.emergency_contact_phone
        ),
    )

    db.add(rider)

    try:
        db.commit()
        db.refresh(rider)

    except Exception:
        db.rollback()
        raise

    return rider


# ============================================================
# GET ALL RIDERS
# ============================================================

@router.get(
    "",
    response_model=list[RiderResponse],
)
def get_riders(
    db: Session = Depends(get_db),
):

    statement = (
        select(Rider)
        .order_by(
            Rider.created_at.desc()
        )
    )

    riders = (
        db.execute(statement)
        .scalars()
        .all()
    )

    return riders


# ============================================================
# GET RIDER
# ============================================================

@router.get(
    "/{rider_id}",
    response_model=RiderResponse,
)
def get_rider(
    rider_id: str,
    db: Session = Depends(get_db),
):

    rider = db.execute(
        select(Rider).where(
            Rider.rider_id == rider_id
        )
    ).scalar_one_or_none()

    if rider is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Rider "
                f"'{rider_id}' "
                "not found."
            ),
        )

    return rider