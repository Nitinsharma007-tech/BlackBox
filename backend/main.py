import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.device import router as device_router
from backend.api.telemetry import router as telemetry_router
from backend.api.black_box import router as black_box_router
from backend.api.events import router as events_router
from backend.api.vehicle import router as vehicle_router
from backend.api.device_vehicle_assignment import (
    router as device_vehicle_assignment_router,
)
from backend.api.rider import router as rider_router
from backend.api.auth import router as auth_router
from backend.api.vehicle_rider_assignment import (
    router as vehicle_rider_assignment_router,
)

from backend.api.parent import router as parent_router
from backend.api.parent_rider_assignment import (
    router as parent_rider_assignment_router,
)
from backend.api.emergency_alert import (
    router as emergency_alert_router,
)
from backend.api.parent_dashboard import (
    router as parent_dashboard_router,
)
from backend.api.safety_status import (
    router as safety_status_router,
)
from backend.api.tracking import (
    router as tracking_router,
)
from backend.api.parent_tracking import (
    router as parent_tracking_router,
)
from backend.api.parent_dashboard_summary import (
    router as parent_dashboard_summary_router,
)
from backend.api.parent_activity import (
    router as parent_activity_router,
)
from backend.api.parent_dashboard_overview import (
    router as parent_dashboard_overview_router,
)

from backend.config import settings

from backend.database import (
    test_mongodb_connection,
    test_postgresql_connection,
)

from backend.database.postgresql import (
    create_tables,
    SessionLocal,
)

from backend.services.emergency_escalation_service import (
    emergency_escalation_service,
)


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="NovaShields Plus IoT Two-Wheeler Safety Platform",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(telemetry_router)

app.include_router(device_router)

app.include_router(black_box_router)

app.include_router(events_router)

app.include_router(vehicle_router)

app.include_router(
    device_vehicle_assignment_router
)

app.include_router(rider_router)

app.include_router(
    vehicle_rider_assignment_router
)

app.include_router(parent_router)

app.include_router(
    parent_rider_assignment_router
)

app.include_router(
    emergency_alert_router
)

app.include_router(
    parent_dashboard_overview_router
)

app.include_router(
    parent_dashboard_summary_router
)

app.include_router(
    parent_activity_router
)

app.include_router(
    parent_dashboard_router
)

app.include_router(
    tracking_router
)

app.include_router(
    parent_tracking_router
)

app.include_router(
    safety_status_router
)

app.include_router(
    auth_router
)


# ============================================================
# EMERGENCY ESCALATION WORKER
# ============================================================

emergency_worker_task = None


async def emergency_escalation_worker():

    print()
    print("=" * 60)
    print("NOVASHIELDS EMERGENCY ESCALATION WORKER")
    print("=" * 60)
    print("Status: STARTED")
    print("Check interval: 1 second")
    print("=" * 60)
    print()

    while True:

        try:

            # ------------------------------------------------
            # Get all currently active incidents
            # ------------------------------------------------

            active_devices = list(
                emergency_escalation_service
                .active_incidents
                .keys()
            )

            # ------------------------------------------------
            # Nothing to process
            # ------------------------------------------------

            if not active_devices:

                await asyncio.sleep(1)

                continue

            # ------------------------------------------------
            # Database session
            # ------------------------------------------------

            if SessionLocal is None:

                print(
                    "Emergency worker: "
                    "SessionLocal unavailable."
                )

                await asyncio.sleep(1)

                continue

            db = SessionLocal()

            try:

                for device_id in active_devices:

                    try:

                        result = (
                            emergency_escalation_service.process(
                                device_id=device_id,
                                crash_still_active=True,
                                db=db,
                            )
                        )

                        if not isinstance(
                            result,
                            dict,
                        ):
                            continue

                        action = result.get(
                            "action"
                        )

                        if action:

                            print()
                            print(
                                "=" * 60
                            )
                            print(
                                "NOVASHIELDS "
                                "BACKGROUND "
                                "EMERGENCY ACTION"
                            )
                            print(
                                "=" * 60
                            )

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
                                result.get(
                                    "status"
                                ),
                            )

                            print(
                                "Alert Created:",
                                result.get(
                                    "alert_created"
                                ),
                            )

                            print(
                                "=" * 60
                            )
                            print()

                    except Exception as error:

                        print()
                        print(
                            "=" * 60
                        )
                        print(
                            "NOVASHIELDS "
                            "EMERGENCY WORKER "
                            "DEVICE ERROR"
                        )

                        print(
                            "Device:",
                            device_id,
                        )

                        print(
                            "Error:",
                            repr(error),
                        )

                        print(
                            "=" * 60
                        )
                        print()

            finally:

                db.close()

            # ------------------------------------------------
            # Check again after 1 second
            # ------------------------------------------------

            await asyncio.sleep(1)

        except asyncio.CancelledError:

            print()
            print(
                "=" * 60
            )
            print(
                "NOVASHIELDS "
                "EMERGENCY WORKER STOPPED"
            )
            print(
                "=" * 60
            )
            print()

            raise

        except Exception as error:

            print()
            print(
                "=" * 60
            )
            print(
                "NOVASHIELDS "
                "EMERGENCY WORKER ERROR"
            )
            print(
                "=" * 60
            )

            print(
                "Error:",
                repr(error),
            )

            print(
                "=" * 60
            )
            print()

            await asyncio.sleep(1)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    global emergency_worker_task

    print()
    print("=" * 60)
    print("NOVASHIELDS PLUS STARTUP")
    print("=" * 60)

    # --------------------------------------------------------
    # Create database tables
    # --------------------------------------------------------

    create_tables()

    print(
        "Database tables: READY"
    )

    # --------------------------------------------------------
    # Start emergency worker
    # --------------------------------------------------------

    emergency_worker_task = (
        asyncio.create_task(
            emergency_escalation_worker()
        )
    )

    print(
        "Emergency escalation worker: STARTED"
    )

    print("=" * 60)
    print()


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event("shutdown")
async def shutdown():

    global emergency_worker_task

    if emergency_worker_task:

        emergency_worker_task.cancel()

        try:

            await emergency_worker_task

        except asyncio.CancelledError:

            pass

        emergency_worker_task = None

    print()
    print("=" * 60)
    print(
        "NOVASHIELDS PLUS SHUTDOWN"
    )
    print(
        "Emergency escalation worker: STOPPED"
    )
    print("=" * 60)
    print()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "project": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "status": "online",
        "message": (
            "NovaShields Plus backend is running"
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "message": (
            "NovaShields Plus backend is running"
        ),
    }


# ============================================================
# DATABASE HEALTH
# ============================================================

@app.get("/health/database")
def database_health():

    postgres = (
        test_postgresql_connection()
    )

    mongodb = (
        test_mongodb_connection()
    )

    overall_status = (
        "healthy"
        if (
            postgres["status"]
            == "connected"
            and
            mongodb["status"]
            == "connected"
        )
        else
        "degraded"
    )

    return {
        "status": overall_status,
        "postgresql": postgres,
        "mongodb": mongodb,
    }