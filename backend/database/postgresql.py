from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import settings


# ============================================================
# DATABASE BASE
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# DATABASE ENGINE
# ============================================================

if settings.DATABASE_URL:

    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
    )

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

else:

    engine = None
    SessionLocal = None


# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():

    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not configured in the .env file."
        )

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# POSTGRESQL CONNECTION TEST
# ============================================================

def test_postgresql_connection():

    if engine is None:

        return {
            "status": "not_configured",
            "message": (
                "DATABASE_URL is not configured."
            ),
        }

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "connected",
            "message": (
                "PostgreSQL connection successful."
            ),
        }

    except Exception as exc:

        return {
            "status": "error",
            "message": str(exc),
        }


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

def create_tables():
    """
    Creates SQLAlchemy tables that do not already exist.

    Existing tables are left untouched.
    """

    if engine is None:

        raise RuntimeError(
            "DATABASE_URL is not configured "
            "in the .env file."
        )

    # --------------------------------------------------------
    # Import all SQLAlchemy models so they are registered
    # with Base.metadata before create_all() runs.
    # --------------------------------------------------------

    from backend.models import (
    Device,
    Telemetry,
    SafetyEvent,
    Vehicle,
    DeviceVehicleAssignment,
    Rider,
    VehicleRiderAssignment,
    Parent,
    ParentRiderAssignment,
    EmergencyAlert,
)

    # --------------------------------------------------------
    # Create only missing tables
    # --------------------------------------------------------

    Base.metadata.create_all(
        bind=engine
    )