from fastapi import APIRouter, HTTPException

from backend.services.black_box_service import black_box_service


# ============================================================
# NOVASHIELDS — BLACK BOX API
# ============================================================
#
# These endpoints expose the real-time rolling black box.
#
# PostgreSQL:
#     Permanent telemetry history
#
# Black Box:
#     Latest 30 seconds of telemetry
#
# ============================================================


router = APIRouter(
    prefix="/api/v1/black-box",
    tags=["Black Box"],
)


# ============================================================
# GET BLACK BOX STATUS
# ============================================================

@router.get(
    "/{device_id}/status"
)
def get_black_box_status(
    device_id: str,
):
    """
    Return the current status of the rolling black box.

    Example response:

    {
        "status": "active",
        "device_id": "NS001",
        "window_seconds": 30,
        "record_count": 30,
        "oldest_timestamp": "...",
        "newest_timestamp": "...",
        "duration_seconds": 29.0,
        "is_frozen": false
    }
    """

    return black_box_service.get_status(
        device_id
    )


# ============================================================
# GET CURRENT BLACK BOX DATA
# ============================================================

@router.get(
    "/{device_id}"
)
def get_black_box(
    device_id: str,
):
    """
    Return the current rolling telemetry buffer.

    This contains only the telemetry currently held
    inside the 30-second black box.
    """

    buffer = black_box_service.get_buffer(
        device_id
    )

    return {
        "status": "active",

        "device_id": device_id,

        "window_seconds": (
            black_box_service.window_seconds
        ),

        "record_count": len(
            buffer
        ),

        "telemetry": buffer,
    }


# ============================================================
# GET FROZEN CRASH EVIDENCE
# ============================================================

@router.get(
    "/{device_id}/evidence"
)
def get_frozen_evidence(
    device_id: str,
):
    """
    Return frozen black-box evidence.

    This endpoint will become especially important
    once the crash detection engine is implemented.
    """

    evidence = (
        black_box_service.get_frozen_evidence(
            device_id
        )
    )

    if not evidence:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No frozen evidence found "
                f"for device {device_id}"
            ),
        )

    return {
        "status": "frozen",

        "device_id": device_id,

        "record_count": len(
            evidence
        ),

        "telemetry": evidence,
    }


# ============================================================
# FREEZE BLACK BOX
# ============================================================

@router.post(
    "/{device_id}/freeze"
)
def freeze_black_box(
    device_id: str,
):
    """
    Manually freeze the current black box.

    IMPORTANT:
    This is only for testing right now.

    Later, the crash detection engine will automatically
    call the Black Box freeze operation.
    """

    result = black_box_service.freeze(
        device_id
    )

    return result


# ============================================================
# RESET BLACK BOX
# ============================================================

@router.post(
    "/{device_id}/reset"
)
def reset_black_box(
    device_id: str,
):
    """
    Reset the black box after an incident/test.

    This is mainly a development/testing operation for now.
    """

    result = black_box_service.reset(
        device_id
    )

    return result