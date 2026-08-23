import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.postgresql import get_db

from backend.models.auth_user import AuthUser
from backend.models.parent import Parent

from backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str, salt: bytes | None = None) -> str:

    if salt is None:
        salt = secrets.token_bytes(16)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200_000,
    )

    return (
        base64.urlsafe_b64encode(salt).decode()
        + "$"
        + base64.urlsafe_b64encode(derived).decode()
    )


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:

    try:

        salt_b64, hash_b64 = stored_hash.split("$", 1)

        salt = base64.urlsafe_b64decode(
            salt_b64.encode()
        )

        expected = base64.urlsafe_b64decode(
            hash_b64.encode()
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            200_000,
        )

        return hmac.compare_digest(
            actual,
            expected,
        )

    except Exception:

        return False


# ============================================================
# TOKEN
# ============================================================

def create_token(user: AuthUser) -> str:

    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "profile_id": user.profile_id,
        "exp": int(time.time()) + 60 * 60 * 24,
    }

    encoded = base64.urlsafe_b64encode(
        json.dumps(
            payload,
            separators=(",", ":"),
        ).encode()
    ).decode()

    return encoded


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):

    # ========================================================
    # FIND USER
    # ========================================================

    user = db.execute(
        select(AuthUser).where(
            AuthUser.email == payload.email
        )
    ).scalar_one_or_none()

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not user.is_active:

        raise HTTPException(
            status_code=403,
            detail="User account is inactive.",
        )

    # ========================================================
    # VERIFY PASSWORD
    # ========================================================

    if not verify_password(
        payload.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    # ========================================================
    # PROFILE
    # ========================================================

    profile = None

    if (
        user.role == "guardian"
        and user.profile_id
    ):

        parent = db.execute(
            select(Parent).where(
                Parent.parent_id
                == user.profile_id
            )
        ).scalar_one_or_none()

        if parent:

            profile = {
                "type": "parent",
                "parent_id": parent.parent_id,
                "full_name": parent.full_name,
                "phone": parent.phone,
                "email": parent.email,
                "is_active": parent.is_active,
            }

    # ========================================================
    # USER RESPONSE
    # ========================================================

    user_data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "profile_id": user.profile_id,
        "is_active": user.is_active,
    }

    # ========================================================
    # TOKEN
    # ========================================================

    token = create_token(user)

    return {
        "token": token,
        "user": user_data,
        "profile": profile,
    }