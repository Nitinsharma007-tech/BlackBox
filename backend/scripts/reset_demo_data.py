from sqlalchemy import delete

from backend.database.postgresql import SessionLocal

from backend.models.telemetry import Telemetry
from backend.models.safety_event import SafetyEvent
from backend.models.emergency_alert import EmergencyAlert


def reset_demo_data():

    db = SessionLocal()

    try:

        print()
        print("=" * 60)
        print("        NOVASHIELDS DEMO DATA RESET")
        print("=" * 60)
        print()

        # =====================================================
        # 1. DELETE EMERGENCY ALERTS
        # =====================================================
        #
        # Alerts contain a foreign key:
        #
        # emergency_alerts.incident_id
        #              ↓
        #       safety_events.id
        #
        # Therefore alerts MUST be deleted first.
        # =====================================================

        alerts_deleted = db.execute(
            delete(EmergencyAlert)
        ).rowcount

        print(
            f"Emergency alerts deleted : "
            f"{alerts_deleted}"
        )

        # =====================================================
        # 2. DELETE SAFETY EVENTS / INCIDENTS
        # =====================================================

        incidents_deleted = db.execute(
            delete(SafetyEvent)
        ).rowcount

        print(
            f"Safety incidents deleted : "
            f"{incidents_deleted}"
        )

        # =====================================================
        # 3. DELETE TELEMETRY
        # =====================================================

        telemetry_deleted = db.execute(
            delete(Telemetry)
        ).rowcount

        print(
            f"Telemetry records deleted : "
            f"{telemetry_deleted}"
        )

        # =====================================================
        # 4. COMMIT
        # =====================================================

        db.commit()

        print()
        print("=" * 60)
        print("NOVASHIELDS RESET COMPLETE")
        print("=" * 60)

        print()
        print("Preserved:")
        print("  ✓ Parent")
        print("  ✓ Rider")
        print("  ✓ Vehicle")
        print("  ✓ Device")
        print("  ✓ Guardian account")

        print()
        print("Cleared:")
        print("  ✓ Emergency alerts")
        print("  ✓ Safety incidents")
        print("  ✓ Telemetry")

        print()
        print("Ready for fresh testing.")
        print("=" * 60)
        print()

    except Exception as error:

        db.rollback()

        print()
        print("=" * 60)
        print("RESET FAILED")
        print("=" * 60)

        print(
            "Error:",
            repr(error)
        )

        print("=" * 60)

        raise

    finally:

        db.close()


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    reset_demo_data()