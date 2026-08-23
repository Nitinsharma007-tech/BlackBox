from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db

from backend.models.emergency_alert import EmergencyAlert
from backend.models.parent import Parent
from backend.models.rider import Rider

from backend.schemas.emergency_alert import (
    EmergencyAlertCreate,
    EmergencyAlertResponse,
)


router = APIRouter(
    prefix="/api/v1/emergency-alerts",
    tags=["Emergency Alerts"],
)


# ============================================================
# CREATE ALERT
# ============================================================

@router.post(
    "",
    response_model=EmergencyAlertResponse,
    status_code=201,
)
def create_alert(
    alert_data: EmergencyAlertCreate,
    db: Session = Depends(get_db),
):

    # --------------------------------------------------------
    # Verify parent
    # --------------------------------------------------------

    parent = db.execute(
        select(Parent).where(
            Parent.parent_id == alert_data.parent_id
        )
    ).scalar_one_or_none()

    if parent is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Parent '{alert_data.parent_id}' "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # Verify rider
    # --------------------------------------------------------

    rider = db.execute(
        select(Rider).where(
            Rider.rider_id == alert_data.rider_id
        )
    ).scalar_one_or_none()

    if rider is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Rider '{alert_data.rider_id}' "
                "not found."
            ),
        )

    # --------------------------------------------------------
    # Prevent duplicate alert IDs
    # --------------------------------------------------------

    existing = db.execute(
        select(EmergencyAlert).where(
            EmergencyAlert.alert_id
            == alert_data.alert_id
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Alert '{alert_data.alert_id}' "
                "already exists."
            ),
        )

    # --------------------------------------------------------
    # Create alert
    # --------------------------------------------------------

    alert = EmergencyAlert(
        alert_id=alert_data.alert_id,
        parent_id=alert_data.parent_id,
        rider_id=alert_data.rider_id,
        vehicle_id=alert_data.vehicle_id,
        device_id=alert_data.device_id,
        incident_id=alert_data.incident_id,
        alert_type=alert_data.alert_type,
        severity=alert_data.severity,
        message=alert_data.message,
        status="pending",
    )

    db.add(alert)

    try:
        db.commit()
        db.refresh(alert)

    except Exception:
        db.rollback()
        raise

    return alert


# ============================================================
# GET ALL ALERTS
# ============================================================

@router.get(
    "",
    response_model=list[EmergencyAlertResponse],
)
def get_alerts(
    db: Session = Depends(get_db),
):

    statement = (
        select(EmergencyAlert)
        .order_by(
            EmergencyAlert.created_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# GET PARENT ALERTS
# ============================================================

@router.get(
    "/parent/{parent_id}",
    response_model=list[EmergencyAlertResponse],
)
def get_parent_alerts(
    parent_id: str,
    db: Session = Depends(get_db),
):

    statement = (
        select(EmergencyAlert)
        .where(
            EmergencyAlert.parent_id == parent_id
        )
        .order_by(
            EmergencyAlert.created_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# GET SINGLE ALERT
# ============================================================

@router.get(
    "/{alert_id}",
    response_model=EmergencyAlertResponse,
)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
):

    alert = db.execute(
        select(EmergencyAlert).where(
            EmergencyAlert.alert_id == alert_id
        )
    ).scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail=f"Alert '{alert_id}' not found.",
        )

    return alert


# ============================================================
# ACKNOWLEDGE ALERT
# ============================================================

@router.post(
    "/{alert_id}/acknowledge",
    response_model=EmergencyAlertResponse,
)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
):

    alert = db.execute(
        select(EmergencyAlert).where(
            EmergencyAlert.alert_id == alert_id
        )
    ).scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail=f"Alert '{alert_id}' not found.",
        )

    if alert.status == "acknowledged":
        raise HTTPException(
            status_code=409,
            detail="Alert is already acknowledged.",
        )

    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(alert)

    except Exception:
        db.rollback()
        raise

    return alert
# ============================================================
# GET PENDING ALERTS FOR PARENT
# ============================================================

@router.get(
    "/parent/{parent_id}/pending",
    response_model=list[EmergencyAlertResponse],
)
def get_pending_parent_alerts(
    parent_id: str,
    db: Session = Depends(get_db),
):
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

    statement = (
        select(EmergencyAlert)
        .where(
            EmergencyAlert.parent_id == parent_id,
            EmergencyAlert.status == "pending",
        )
        .order_by(
            EmergencyAlert.created_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# ACKNOWLEDGE ALERT FOR PARENT
# ============================================================

@router.post(
    "/parent/{parent_id}/{alert_id}/acknowledge",
    response_model=EmergencyAlertResponse,
)
def acknowledge_parent_alert(
    parent_id: str,
    alert_id: str,
    db: Session = Depends(get_db),
):
    alert = db.execute(
        select(EmergencyAlert).where(
            EmergencyAlert.alert_id == alert_id,
            EmergencyAlert.parent_id == parent_id,
        )
    ).scalar_one_or_none()

    if alert is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Alert '{alert_id}' was not found "
                f"for parent '{parent_id}'."
            ),
        )

    if alert.status == "acknowledged":
        raise HTTPException(
            status_code=409,
            detail="Alert is already acknowledged.",
        )

    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(alert)

    except Exception:
        db.rollback()
        raise

    return alert