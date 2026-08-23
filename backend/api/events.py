from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from backend.database.postgresql import get_db
from backend.models.safety_event import SafetyEvent
from backend.schemas.safety_event import SafetyEventResponse


router = APIRouter(
    prefix="/api/v1/events",
    tags=["Safety Events"],
)


# ============================================================
# GET ALL EVENTS FOR DEVICE
# ============================================================

@router.get(
    "/{device_id}",
    response_model=list[SafetyEventResponse],
)
def get_device_events(
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
        select(SafetyEvent)
        .where(
            SafetyEvent.device_id == device_id
        )
        .order_by(
            SafetyEvent.timestamp.desc()
        )
        .limit(limit)
    )

    events = (
        db.execute(statement)
        .scalars()
        .all()
    )

    return events


# ============================================================
# GET LATEST EVENT
# ============================================================

@router.get(
    "/{device_id}/latest",
    response_model=SafetyEventResponse,
)
def get_latest_event(
    device_id: str,
    db: Session = Depends(get_db),
):

    statement = (
        select(SafetyEvent)
        .where(
            SafetyEvent.device_id == device_id
        )
        .order_by(
            SafetyEvent.timestamp.desc()
        )
        .limit(1)
    )

    event = (
        db.execute(statement)
        .scalar_one_or_none()
    )

    if event is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No safety events found "
                f"for device {device_id}"
            ),
        )

    return event


# ============================================================
# GET EVENT BY ID
# ============================================================

@router.get(
    "/event/{event_id}",
    response_model=SafetyEventResponse,
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):

    event = db.get(
        SafetyEvent,
        event_id
    )

    if event is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Safety event {event_id} "
                "not found."
            ),
        )

    return event
@router.patch(
    "/{event_id}/acknowledge",
    response_model=SafetyEventResponse,
)
def acknowledge_event(
    event_id: int,
    db: Session = Depends(get_db),
):

    event = db.get(
        SafetyEvent,
        event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Safety event {event_id} not found.",
        )

    if event.status != "detected":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Event cannot be acknowledged "
                f"from status '{event.status}'."
            ),
        )

    event.status = "acknowledged"

    db.commit()
    db.refresh(event)

    return event
@router.patch(
    "/{event_id}/review",
    response_model=SafetyEventResponse,
)
def review_event(
    event_id: int,
    db: Session = Depends(get_db),
):

    event = db.get(
        SafetyEvent,
        event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Safety event {event_id} not found.",
        )

    if event.status != "acknowledged":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Event cannot enter review "
                f"from status '{event.status}'."
            ),
        )

    event.status = "under_review"

    db.commit()
    db.refresh(event)

    return event
@router.patch(
    "/{event_id}/resolve",
    response_model=SafetyEventResponse,
)
def resolve_event(
    event_id: int,
    db: Session = Depends(get_db),
):

    event = db.get(
        SafetyEvent,
        event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Safety event {event_id} not found.",
        )

    if event.status != "under_review":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Event cannot be resolved "
                f"from status '{event.status}'."
            ),
        )

    event.status = "resolved"

    db.commit()
    db.refresh(event)

    return event