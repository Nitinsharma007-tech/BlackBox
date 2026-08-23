from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db
from backend.models.parent import Parent
from backend.schemas.parent import (
    ParentCreate,
    ParentResponse,
)


router = APIRouter(
    prefix="/api/v1/parents",
    tags=["Parents"],
)


# ============================================================
# CREATE PARENT
# ============================================================

@router.post(
    "",
    response_model=ParentResponse,
    status_code=201,
)
def create_parent(
    parent_data: ParentCreate,
    db: Session = Depends(get_db),
):

    existing_parent = db.execute(
        select(Parent).where(
            Parent.parent_id == parent_data.parent_id
        )
    ).scalar_one_or_none()

    if existing_parent is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Parent '{parent_data.parent_id}' "
                "already exists."
            ),
        )

    parent = Parent(
        parent_id=parent_data.parent_id,
        full_name=parent_data.full_name,
        phone=parent_data.phone,
        email=parent_data.email,
    )

    db.add(parent)

    try:
        db.commit()
        db.refresh(parent)

    except Exception:
        db.rollback()
        raise

    return parent


# ============================================================
# GET ALL PARENTS
# ============================================================

@router.get(
    "",
    response_model=list[ParentResponse],
)
def get_parents(
    db: Session = Depends(get_db),
):

    statement = (
        select(Parent)
        .order_by(
            Parent.created_at.desc()
        )
    )

    return (
        db.execute(statement)
        .scalars()
        .all()
    )


# ============================================================
# GET PARENT
# ============================================================

@router.get(
    "/{parent_id}",
    response_model=ParentResponse,
)
def get_parent(
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
            detail=(
                f"Parent '{parent_id}' "
                "not found."
            ),
        )

    return parent