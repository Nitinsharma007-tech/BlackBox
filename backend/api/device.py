from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db
from backend.models.device import Device
from backend.schemas.device import DeviceCreate, DeviceResponse


router = APIRouter(
    prefix="/api/v1/devices",
    tags=["Devices"],
)


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=201,
)
def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
):
    existing_device = db.execute(
        select(Device).where(
            Device.device_id == device_data.device_id
        )
    ).scalar_one_or_none()

    if existing_device:
        raise HTTPException(
            status_code=409,
            detail="Device already exists.",
        )

    device = Device(
        device_id=device_data.device_id,
        name=device_data.name,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


@router.get(
    "",
    response_model=list[DeviceResponse],
)
def get_devices(
    db: Session = Depends(get_db),
):
    statement = select(Device).order_by(Device.id)

    return db.execute(statement).scalars().all()


@router.get(
    "/{device_id}",
    response_model=DeviceResponse,
)
def get_device(
    device_id: str,
    db: Session = Depends(get_db),
):
    device = db.execute(
        select(Device).where(
            Device.device_id == device_id
        )
    ).scalar_one_or_none()

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found.",
        )

    return device