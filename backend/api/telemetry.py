from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db

from backend.models.device import Device
from backend.models.telemetry import Telemetry
from backend.models.safety_event import SafetyEvent
from backend.models.emergency_alert import EmergencyAlert

from backend.schemas.telemetry import (
    TelemetryCreate,
    TelemetryResponse,
)

from backend.services.black_box_service import (
    black_box_service,
)

from backend.services.safety_event_service import (
    safety_event_service,
)

from backend.services.emergency_escalation_service import (
    emergency_escalation_service,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/telemetry",
    tags=["Telemetry"],
)


# ============================================================
# HELPERS
# ============================================================

def get_active_crash_incident(
    db: Session,
    device_id: str,
):
    """
    Return the latest active crash incident for a device.

    This prevents every crash telemetry packet from creating
    another SafetyEvent.

    A crash is considered active when its SafetyEvent status
    has not been explicitly resolved/cancelled/closed.
    """

    statement = (
        select(SafetyEvent)
        .where(
            SafetyEvent.device_id == device_id,
            SafetyEvent.event_type == "crash",
        )
        .order_by(
            SafetyEvent.created_at.desc()
        )
        .limit(1)
    )

    latest_crash = (
        db.execute(statement)
        .scalar_one_or_none()
    )

    if latest_crash is None:
        return None

    status = (
        str(
            getattr(
                latest_crash,
                "status",
                "detected",
            )
        )
        .lower()
        .strip()
    )

    # These statuses mean the incident has ended.
    resolved_statuses = {
        "resolved",
        "cancelled",
        "canceled",
        "closed",
        "completed",
    }

    if status in resolved_statuses:
        return None

    return latest_crash


def is_emergency_active(
    status_result: dict | None,
) -> bool:
    """
    Determine whether an emergency escalation is currently
    active for the device.

    This intentionally accepts several possible status names
    so it remains compatible with the emergency escalation
    service.
    """

    if not isinstance(
        status_result,
        dict,
    ):
        return False

    if status_result.get(
        "active"
    ) is True:

        return True

    status = str(
        status_result.get(
            "status",
            "",
        )
    ).lower().strip()

    active_statuses = {
        "active",
        "waiting_for_rider",
        "awaiting_rider",
        "awaiting_rider_response",
        "pending",
        "escalating",
        "parent_pending",
        "ambulance_pending",
        "police_pending",
    }

    return status in active_statuses


# ============================================================
# CREATE TELEMETRY
# ============================================================

@router.post(
    "",
    response_model=TelemetryResponse,
    status_code=201,
)
def create_telemetry(
    telemetry_data: TelemetryCreate,
    db: Session = Depends(get_db),
):

    device_id = (
        telemetry_data.device_id
    )

    # ========================================================
    # 1. VERIFY DEVICE EXISTS
    # ========================================================

    device = db.execute(
        select(Device).where(
            Device.device_id
            == device_id
        )
    ).scalar_one_or_none()

    if device is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Device '{device_id}' "
                "not found."
            ),
        )

    # ========================================================
    # 2. CREATE DATABASE TELEMETRY RECORD
    # ========================================================

    telemetry = Telemetry(

        device_id=device_id,

        timestamp=(
            telemetry_data.timestamp
        ),

        latitude=(
            telemetry_data.latitude
        ),

        longitude=(
            telemetry_data.longitude
        ),

        speed=(
            telemetry_data.speed
        ),

        acceleration_x=(
            telemetry_data.acceleration_x
        ),

        acceleration_y=(
            telemetry_data.acceleration_y
        ),

        acceleration_z=(
            telemetry_data.acceleration_z
        ),

        gyro_x=(
            telemetry_data.gyro_x
        ),

        gyro_y=(
            telemetry_data.gyro_y
        ),

        gyro_z=(
            telemetry_data.gyro_z
        ),

        roll=(
            telemetry_data.roll
        ),

        pitch=(
            telemetry_data.pitch
        ),
    )

    db.add(telemetry)

    # ========================================================
    # 3. UPDATE DEVICE LAST SEEN
    # ========================================================

    if (
        device.last_seen is None
        or
        telemetry_data.timestamp
        > device.last_seen
    ):

        device.last_seen = (
            telemetry_data.timestamp
        )

    # ========================================================
    # 4. SAVE TELEMETRY
    # ========================================================

    try:

        db.commit()

        db.refresh(
            telemetry
        )

    except Exception:

        db.rollback()

        raise

    # ========================================================
    # 5. CONVERT TELEMETRY FOR BLACK BOX
    # ========================================================

    black_box_telemetry = {

        "device_id": device_id,

        "timestamp": (
            telemetry_data.timestamp
            .isoformat()
        ),

        "latitude": (
            telemetry_data.latitude
        ),

        "longitude": (
            telemetry_data.longitude
        ),

        "speed": (
            telemetry_data.speed
        ),

        "acceleration_x": (
            telemetry_data.acceleration_x
        ),

        "acceleration_y": (
            telemetry_data.acceleration_y
        ),

        "acceleration_z": (
            telemetry_data.acceleration_z
        ),

        "gyro_x": (
            telemetry_data.gyro_x
        ),

        "gyro_y": (
            telemetry_data.gyro_y
        ),

        "gyro_z": (
            telemetry_data.gyro_z
        ),

        "roll": (
            telemetry_data.roll
        ),

        "pitch": (
            telemetry_data.pitch
        ),
    }

    # ========================================================
    # 6. UPDATE ROLLING BLACK BOX
    # ========================================================

    try:

        black_box_result = (
            black_box_service.add_telemetry(
                black_box_telemetry
            )
        )

        current_buffer = (
            black_box_service.get_buffer(
                device_id
            )
        )

        print()
        print("=" * 60)
        print(
            "NOVASHIELDS BLACK BOX"
        )
        print("=" * 60)

        print(
            "Device:",
            device_id
        )

        print(
            "Timestamp:",
            telemetry_data.timestamp
        )

        print(
            "Speed:",
            telemetry_data.speed
        )

        print(
            "Roll:",
            telemetry_data.roll
        )

        print(
            "Pitch:",
            telemetry_data.pitch
        )

        print(
            "Accel-Z:",
            telemetry_data.acceleration_z
        )

        print(
            "Black Box Result:",
            black_box_result
        )

        print(
            "Current Buffer Size:",
            len(current_buffer)
        )

        print("=" * 60)

    except Exception as error:

        print()
        print("=" * 60)
        print(
            "NOVASHIELDS BLACK BOX ERROR"
        )
        print("=" * 60)

        print(
            "Error:",
            repr(error)
        )

        print("=" * 60)

    # ========================================================
    # 7. SAFETY EVENT DETECTION
    #
    # CURRENT SAFETY EVENTS:
    #
    #   OVERSPEED
    #   POTHOLE / IMPACT
    #   CRASH / FALL
    #
    # HARD BRAKING AND AGGRESSIVE TURN ARE NOT USED.
    # ========================================================

    try:

        event_result = (
            safety_event_service.analyze(
                black_box_telemetry
            )
        )

        print()
        print("=" * 60)
        print(
            "NOVASHIELDS SAFETY EVENT DETECTION"
        )
        print("=" * 60)

        print(
            "Device:",
            device_id
        )

        print(
            "Event Detected:",
            event_result.get(
                "event_detected"
            )
        )

        print(
            "Event Type:",
            event_result.get(
                "event_type"
            )
        )

        print(
            "Severity:",
            event_result.get(
                "severity"
            )
        )

        print(
            "Message:",
            event_result.get(
                "message"
            )
        )

        print(
            "Speed:",
            event_result.get(
                "speed"
            )
        )

        print(
            "Accel-Z:",
            event_result.get(
                "acceleration_z"
            )
        )

        print(
            "Roll:",
            event_result.get(
                "roll"
            )
        )

        print(
            "Pitch:",
            event_result.get(
                "pitch"
            )
        )

        print(
            "Calibrated Roll:",
            event_result.get(
                "calibrated_roll"
            )
        )

        print(
            "Calibrated Pitch:",
            event_result.get(
                "calibrated_pitch"
            )
        )

        print(
            "Roll Deviation:",
            event_result.get(
                "roll_deviation"
            )
        )

        print(
            "Pitch Deviation:",
            event_result.get(
                "pitch_deviation"
            )
        )

        print("=" * 60)

    except Exception as error:

        print()
        print("=" * 60)
        print(
            "NOVASHIELDS SAFETY DETECTION ERROR"
        )
        print("=" * 60)

        print(
            "Error:",
            repr(error)
        )

        print("=" * 60)

        event_result = {

            "event_detected": False,

            "event_type": None,

            "severity": "unknown",

            "message":
                "Safety detection failed.",
        }

    # ========================================================
    # 8. SAFETY EVENT PROCESSING
    # ========================================================

    if event_result.get(
        "event_detected",
        False,
    ):

        event_type = event_result.get(
            "event_type"
        )

        # ====================================================
        # CRASH
        # ====================================================

        if event_type == "crash":

            try:

                # ------------------------------------------------
                # CHECK FOR EXISTING ACTIVE CRASH
                # ------------------------------------------------

                statement = (
                    select(SafetyEvent)
                    .where(
                        SafetyEvent.device_id == device_id,
                        SafetyEvent.event_type == "crash",
                    )
                    .order_by(
                        SafetyEvent.created_at.desc()
                    )
                    .limit(1)
                )

                existing_crash = (
                    db.execute(statement)
                    .scalar_one_or_none()
                )

                # ------------------------------------------------
                # CHECK WHETHER EXISTING INCIDENT IS CLOSED
                # ------------------------------------------------

                active_crash = False

                if existing_crash is not None:

                    existing_status = str(
                        getattr(
                            existing_crash,
                            "status",
                            "detected",
                        )
                    ).lower()

                    if existing_status not in {
                        "resolved",
                        "cancelled",
                        "canceled",
                        "closed",
                        "completed",
                    }:

                        active_crash = True

                # ------------------------------------------------
                # DUPLICATE CRASH
                # ------------------------------------------------

                if active_crash:

                    print()
                    print("=" * 60)
                    print(
                        "NOVASHIELDS ACTIVE CRASH"
                    )
                    print("=" * 60)

                    print(
                        "Device:",
                        device_id,
                    )

                    print(
                        "Existing Event ID:",
                        existing_crash.id,
                    )

                    print(
                        "New crash packet:",
                        "IGNORED AS DUPLICATE",
                    )

                    print("=" * 60)
                    print()

                # ------------------------------------------------
                # FIRST CRASH
                # ------------------------------------------------

                else:

                    # ------------------------------------------------
                    # CHECK BLACK BOX
                    # ------------------------------------------------

                    black_box_status = (
                        black_box_service.get_status(
                            device_id
                        )
                    )

                    is_frozen = (
                        black_box_status.get(
                            "is_frozen",
                            False,
                        )
                    )

                    # ------------------------------------------------
                    # FREEZE BLACK BOX
                    # ------------------------------------------------

                    if not is_frozen:

                        freeze_result = (
                            black_box_service.freeze(
                                device_id
                            )
                        )

                        frozen_evidence_count = (
                            freeze_result.get(
                                "record_count",
                                0,
                            )
                        )

                    else:

                        current_buffer = (
                            black_box_service.get_buffer(
                                device_id
                            )
                        )

                        frozen_evidence_count = (
                            len(current_buffer)
                        )

                    # ------------------------------------------------
                    # CREATE ONE CRASH EVENT
                    # ------------------------------------------------

                    safety_event = SafetyEvent(

                        device_id=device_id,

                        event_type="crash",

                        severity=(
                            event_result.get(
                                "severity",
                                "critical",
                            )
                        ),

                        message=(
                            event_result.get(
                                "message",
                                "Potential crash detected.",
                            )
                        ),

                        timestamp=(
                            telemetry_data.timestamp
                        ),

                        latitude=(
                            telemetry_data.latitude
                        ),

                        longitude=(
                            telemetry_data.longitude
                        ),

                        speed=(
                            telemetry_data.speed
                        ),

                        black_box_frozen=True,

                        frozen_evidence_count=(
                            frozen_evidence_count
                        ),
                    )

                    db.add(
                        safety_event
                    )

                    db.commit()

                    db.refresh(
                        safety_event
                    )

                    # ------------------------------------------------
                    # INCIDENT LOG
                    # ------------------------------------------------

                    print()
                    print("=" * 60)
                    print(
                        "NOVASHIELDS INCIDENT CREATED"
                    )
                    print("=" * 60)

                    print(
                        "Event ID:",
                        safety_event.id,
                    )

                    print(
                        "Device:",
                        safety_event.device_id,
                    )

                    print(
                        "Event:",
                        safety_event.event_type,
                    )

                    print(
                        "Severity:",
                        safety_event.severity,
                    )

                    print(
                        "Speed:",
                        safety_event.speed,
                    )

                    print(
                        "Black Box:",
                        "FROZEN",
                    )

                    print(
                        "Evidence:",
                        safety_event.frozen_evidence_count,
                        "records",
                    )

                    print("=" * 60)
                    print()

                    # ------------------------------------------------
                    # START EMERGENCY ESCALATION
                    # ------------------------------------------------

                    try:

                        crash_event = {

                            "incident_id":
                                safety_event.id,

                            "device_id":
                                device_id,

                            "event_type":
                                "crash",

                            "severity":
                                safety_event.severity,

                            "message":
                                safety_event.message,

                            "timestamp":
                                telemetry_data
                                .timestamp
                                .isoformat(),

                            "latitude":
                                telemetry_data.latitude,

                            "longitude":
                                telemetry_data.longitude,

                            "speed":
                                telemetry_data.speed,

                            "roll":
                                telemetry_data.roll,

                            "pitch":
                                telemetry_data.pitch,

                            "calibrated_roll":
                                event_result.get(
                                    "calibrated_roll"
                                ),

                            "calibrated_pitch":
                                event_result.get(
                                    "calibrated_pitch"
                                ),

                            "roll_deviation":
                                event_result.get(
                                    "roll_deviation"
                                ),

                            "pitch_deviation":
                                event_result.get(
                                    "pitch_deviation"
                                ),

                            "max_angle_deviation":
                                event_result.get(
                                    "max_angle_deviation"
                                ),
                        }

                        escalation = (
                            emergency_escalation_service
                            .start_crash(
                                device_id=device_id,

                                crash_event=(
                                    crash_event
                                ),

                                db=db,
                            )
                        )

                        print()
                        print("=" * 60)
                        print(
                            "NOVASHIELDS CRASH ESCALATION"
                        )
                        print("=" * 60)

                        print(
                            "Device:",
                            device_id,
                        )

                        print(
                            "Incident:",
                            safety_event.id,
                        )

                        print(
                            "Escalation Status:",
                            escalation.get(
                                "status"
                            ),
                        )

                        print(
                            "Rider Response:",
                            "30 seconds",
                        )

                        print(
                            "Parent + Ambulance:",
                            "After rider timeout",
                        )

                        print(
                            "Police:",
                            "After 30 minutes "
                            "if unresolved",
                        )

                        print("=" * 60)
                        print()

                    except Exception as emergency_error:

                        print()
                        print("=" * 60)
                        print(
                            "NOVASHIELDS EMERGENCY "
                            "ESCALATION ERROR"
                        )
                        print("=" * 60)

                        print(
                            "Error:",
                            repr(
                                emergency_error
                            ),
                        )

                        print("=" * 60)
                        print()

            except Exception as error:

                db.rollback()

                print()
                print("=" * 60)
                print(
                    "NOVASHIELDS CRASH PROCESSING ERROR"
                )
                print("=" * 60)

                print(
                    "Error:",
                    repr(error),
                )

                print("=" * 60)
                print()

        # ====================================================
        # NON-CRASH EVENTS
        # ====================================================

        elif event_type in {
            "overspeed",
            "pothole",
        }:

            try:

                safety_event = SafetyEvent(

                    device_id=device_id,

                    event_type=event_type,

                    severity=(
                        event_result.get(
                            "severity",
                            "medium",
                        )
                    ),

                    message=(
                        event_result.get(
                            "message",
                            "Safety event detected.",
                        )
                    ),

                    timestamp=(
                        telemetry_data.timestamp
                    ),

                    latitude=(
                        telemetry_data.latitude
                    ),

                    longitude=(
                        telemetry_data.longitude
                    ),

                    speed=(
                        telemetry_data.speed
                    ),

                    black_box_frozen=False,

                    frozen_evidence_count=0,
                )

                db.add(
                    safety_event
                )

                db.commit()

                db.refresh(
                    safety_event
                )

                print()
                print("=" * 60)
                print(
                    "NOVASHIELDS SAFETY EVENT"
                )
                print("=" * 60)

                print(
                    "Event ID:",
                    safety_event.id,
                )

                print(
                    "Device:",
                    device_id,
                )

                print(
                    "Event:",
                    event_type,
                )

                print(
                    "Severity:",
                    safety_event.severity,
                )

                print(
                    "Emergency Escalation:",
                    "NOT STARTED",
                )

                print("=" * 60)
                print()

            except Exception as error:

                db.rollback()

                print()
                print("=" * 60)
                print(
                    "NOVASHIELDS SAFETY EVENT "
                    "DATABASE ERROR"
                )
                print("=" * 60)

                print(
                    "Error:",
                    repr(error),
                )

                print("=" * 60)
                print()

    # ========================================================
    # 9. EXISTING EMERGENCY ESCALATION PROCESSING
    # ========================================================

    try:

        emergency_status = (
            emergency_escalation_service
            .get_status(
                device_id
            )
        )

        if isinstance(
            emergency_status,
            dict,
        ):

            status = str(
                emergency_status.get(
                    "status",
                    "",
                )
            ).lower()

            emergency_active = (
                emergency_status.get(
                    "active",
                    False,
                )
                or status in {
                    "active",
                    "waiting_for_rider",
                    "awaiting_rider",
                    "awaiting_rider_response",
                    "pending",
                    "escalating",
                    "parent_pending",
                    "ambulance_pending",
                    "police_pending",
                }
            )

            if emergency_active:

                escalation_status = (
                    emergency_escalation_service
                    .process(
                        device_id,
                        crash_still_active=True,
                        db=db,
                    )
                )

                action = (
                    escalation_status.get(
                        "action"
                    )
                )

                if action:

                    print()
                    print("=" * 60)
                    print(
                        "NOVASHIELDS EMERGENCY ACTION"
                    )
                    print("=" * 60)

                    print(
                        "Device:",
                        device_id,
                    )

                    print(
                        "Action:",
                        action,
                    )

                    print(
                        "Status:",
                        escalation_status.get(
                            "status"
                        ),
                    )

                    print("=" * 60)
                    print()

    except Exception as emergency_error:

        print()
        print("=" * 60)
        print(
            "NOVASHIELDS EMERGENCY "
            "PROCESSING ERROR"
        )
        print("=" * 60)

        print(
            "Error:",
            repr(
                emergency_error
            ),
        )

        print("=" * 60)
        print()

# ========================================================
    # 10. RETURN TELEMETRY
    # ========================================================

    return telemetry


# ============================================================
# RIDER CONFIRMS "I'M OK"
# ============================================================

@router.post(
    "/emergency/{device_id}/rider-ok"
)
def rider_is_ok(
    device_id: str,
):

    result = (
        emergency_escalation_service
        .rider_is_ok(
            device_id
        )
    )

    if not result.get(
        "success",
        False,
    ):

        raise HTTPException(
            status_code=409,
            detail=result.get(
                "message",
                "Unable to cancel emergency.",
            ),
        )

    return result


# ============================================================
# GET CURRENT EMERGENCY STATUS
# ============================================================

@router.get(
    "/emergency/{device_id}/status"
)
def get_emergency_status(
    device_id: str,
):

    return (
        emergency_escalation_service
        .get_status(
            device_id
        )
    )


# ============================================================
# GET LATEST TELEMETRY
# ============================================================

@router.get(
    "/latest/{device_id}",
    response_model=TelemetryResponse,
)
def get_latest_telemetry(
    device_id: str,
    db: Session = Depends(get_db),
):

    statement = (
        select(Telemetry)
        .where(
            Telemetry.device_id
            == device_id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(1)
    )

    telemetry = db.execute(
        statement
    ).scalar_one_or_none()

    if telemetry is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No telemetry found "
                f"for device {device_id}"
            ),
        )

    return telemetry


# ============================================================
# GET DEVICE TELEMETRY
# ============================================================

@router.get(
    "/device/{device_id}",
    response_model=list[TelemetryResponse],
)
def get_device_telemetry(
    device_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
):

    if limit < 1 or limit > 1000:

        raise HTTPException(
            status_code=400,
            detail=(
                "limit must be between 1 and 1000"
            ),
        )

    statement = (
        select(Telemetry)
        .where(
            Telemetry.device_id
            == device_id
        )
        .order_by(
            Telemetry.timestamp.desc()
        )
        .limit(limit)
    )

    telemetry_records = (
        db.execute(
            statement
        )
        .scalars()
        .all()
    )

    return telemetry_records