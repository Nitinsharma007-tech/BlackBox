from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db
from backend.models.vehicle import Vehicle
from backend.schemas.vehicle import (
    VehicleCreate,
    VehicleResponse,
)


router = APIRouter(
    prefix="/api/v1/vehicles",
    tags=["Vehicles"],
)


# ============================================================
# CREATE VEHICLE
# ============================================================

@router.post(
    "",
    response_model=VehicleResponse,
    status_code=201,
)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Check vehicle ID
    # --------------------------------------------------------

    existing_vehicle = db.execute(
        select(Vehicle).where(
            Vehicle.vehicle_id
            == vehicle_data.vehicle_id
        )
    ).scalar_one_or_none()

    if existing_vehicle is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                f"Vehicle "
                f"'{vehicle_data.vehicle_id}' "
                f"already exists."
            ),
        )

    # --------------------------------------------------------
    # Check registration number
    # --------------------------------------------------------

    existing_registration = db.execute(
        select(Vehicle).where(
            Vehicle.registration_number
            == vehicle_data.registration_number
        )
    ).scalar_one_or_none()

    if existing_registration is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                "Vehicle with registration number "
                f"'{vehicle_data.registration_number}' "
                "already exists."
            ),
        )

    # --------------------------------------------------------
    # Create vehicle
    # --------------------------------------------------------

    vehicle = Vehicle(
        vehicle_id=vehicle_data.vehicle_id,
        registration_number=(
            vehicle_data.registration_number
        ),
        make=vehicle_data.make,
        model=vehicle_data.model,
        year=vehicle_data.year,
    )

    db.add(vehicle)

    try:

        db.commit()

        db.refresh(vehicle)

    except Exception:

        db.rollback()

        raise

    return vehicle


# ============================================================
# GET VEHICLE
# ============================================================

@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
):

    vehicle = db.execute(
        select(Vehicle).where(
            Vehicle.vehicle_id == vehicle_id
        )
    ).scalar_one_or_none()

    if vehicle is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Vehicle '{vehicle_id}' "
                "not found."
            ),
        )

    return vehicle


# ============================================================
# GET ALL VEHICLES
# ============================================================

@router.get(
    "",
    response_model=list[VehicleResponse],
)
def get_vehicles(
    db: Session = Depends(get_db),
):

    statement = (
        select(Vehicle)
        .order_by(
            Vehicle.created_at.desc()
        )
    )

    vehicles = (
        db.execute(statement)
        .scalars()
        .all()
    )

    return vehicles