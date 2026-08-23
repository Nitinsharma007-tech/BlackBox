from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, inspect
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

from backend.schemas.parent_dashboard import (
    ParentDashboardResponse,
)

from backend.services.safety_status_service import (
    safety_status_service,
)


router = APIRouter(
    prefix="/api/v1/parent-dashboard",
    tags=["Parent Dashboard"],
)


# ============================================================
# SQLALCHEMY OBJECT → DICTIONARY
# ============================================================

def model_to_dict(model):
    """
    Convert a SQLAlchemy model instance into a plain dictionary.

    Only database columns are included.
    SQLAlchemy relationships are intentionally ignored.
    """

    if model is None:
        return None

    return {
        column.key: getattr(model, column.key)
        for column in inspect(model).mapper.column_attrs
    }


# ============================================================
# PARENT DASHBOARD
# ============================================================

@router.get(
    "/{parent_id}",
    response_model=ParentDashboardResponse,
)
def get_parent_dashboard(
    parent_id: str,
    db: Session = Depends(get_db),
):

    # ========================================================
    # 1. PARENT
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

    parent_data = model_to_dict(parent)

    # ========================================================
    # 2. PARENT → RIDERS
    # ========================================================

    assignments = db.execute(
        select(ParentRiderAssignment).where(
            ParentRiderAssignment.parent_id == parent_id,
            ParentRiderAssignment.status == "active",
        )
    ).scalars().all()

    riders_data = []

    for assignment in assignments:

        # ====================================================
        # GET RIDER
        # ====================================================

        rider = db.execute(
            select(Rider).where(
                Rider.rider_id == assignment.rider_id
            )
        ).scalar_one_or_none()

        if rider is None:
            continue

        rider_data = model_to_dict(rider)

        # ====================================================
        # RIDER → VEHICLE
        # ====================================================

        vehicle_assignment = db.execute(
            select(VehicleRiderAssignment).where(
                VehicleRiderAssignment.rider_id
                == rider.rider_id,
                VehicleRiderAssignment.status
                == "active",
            )
        ).scalar_one_or_none()

        vehicle = None
        device = None
        latest_telemetry = None

        # ====================================================
        # GET VEHICLE
        # ====================================================

        if vehicle_assignment:

            vehicle = db.execute(
                select(Vehicle).where(
                    Vehicle.vehicle_id
                    == vehicle_assignment.vehicle_id
                )
            ).scalar_one_or_none()

        vehicle_data = model_to_dict(vehicle)

        # ====================================================
        # VEHICLE → DEVICE
        # ====================================================

        if vehicle:

            device_assignment = db.execute(
                select(DeviceVehicleAssignment).where(
                    DeviceVehicleAssignment.vehicle_id
                    == vehicle.vehicle_id,
                    DeviceVehicleAssignment.status
                    == "active",
                )
            ).scalar_one_or_none()

            if device_assignment:

                device = db.execute(
                    select(Device).where(
                        Device.device_id
                        == device_assignment.device_id
                    )
                ).scalar_one_or_none()

        device_data = model_to_dict(device)

        # ====================================================
        # LATEST TELEMETRY
        # ====================================================

        if device:

            latest_telemetry = db.execute(
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

        telemetry_data = model_to_dict(
            latest_telemetry
        )

        # ====================================================
        # RECENT SAFETY INCIDENTS
        # ====================================================

        if device:

            recent_incidents = db.execute(
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

        else:

            recent_incidents = []

        incidents_data = [
            model_to_dict(incident)
            for incident in recent_incidents
        ]

        # ====================================================
        # LIVE SAFETY STATUS
        # ====================================================

        safety_status = (
            safety_status_service.calculate_status(
                device=device,
                latest_telemetry=latest_telemetry,
                recent_incidents=recent_incidents,
            )
        )

        # ====================================================
        # EMERGENCY ALERTS
        # ====================================================

        alerts = db.execute(
            select(EmergencyAlert)
            .where(
                EmergencyAlert.parent_id == parent_id,
                EmergencyAlert.rider_id == rider.rider_id,
            )
            .order_by(
                EmergencyAlert.created_at.desc()
            )
            .limit(10)
        ).scalars().all()

        alerts_data = [
            model_to_dict(alert)
            for alert in alerts
        ]

        # ====================================================
        # RIDER DASHBOARD DATA
        # ====================================================

        riders_data.append(
            {
                "rider": rider_data,

                "vehicle": vehicle_data,

                "device": device_data,

                "latest_telemetry": telemetry_data,

                "safety_status": safety_status,

                "recent_incidents": incidents_data,

                "alerts": alerts_data,
            }
        )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "parent": parent_data,
        "riders": riders_data,
    }