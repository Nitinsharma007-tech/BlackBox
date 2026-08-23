from sqlalchemy import select

from backend.database.postgresql import SessionLocal

from backend.models.auth_user import AuthUser
from backend.models.parent import Parent

from backend.api.auth import hash_password


EMAIL = "parent@novashields.local"
PASSWORD = "Nova@12345"


def main():

    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    db = SessionLocal()

    try:

        parent = db.execute(
            select(Parent).where(
                Parent.parent_id == "PT001"
            )
        ).scalar_one_or_none()

        if parent is None:
            print("Parent PT001 does not exist.")
            return

        existing = db.execute(
            select(AuthUser).where(
                AuthUser.email == EMAIL
            )
        ).scalar_one_or_none()

        if existing:
            print("Authentication user already exists.")
            return

        user = AuthUser(
            email=EMAIL,
            password_hash=hash_password(PASSWORD),
            role="guardian",
            profile_id=parent.parent_id,
            is_active=True,
        )

        db.add(user)
        db.commit()

        print("Guardian authentication user created.")
        print(f"Email: {EMAIL}")
        print(f"Password: {PASSWORD}")
        print(f"Parent: {parent.parent_id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()