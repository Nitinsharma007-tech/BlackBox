from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.emergency_alert import EmergencyAlert
from backend.models.parent_rider_assignment import (
    ParentRiderAssignment,
)
from backend.models.vehicle_rider_assignment import (
    VehicleRiderAssignment,
)
from backend.models.device_vehicle_assignment import (
    DeviceVehicleAssignment,
)


class EmergencyEscalationService:
    """
    NovaShields Emergency Escalation Service.

    Crash escalation flow:

        CRASH DETECTED
              |
              v
        30 second rider window
              |
        +-----+------+
        |            |
      I'M OK      No response
        |            |
        v            v
      CANCEL    PARENT + AMBULANCE
                     |
                     v
               30 minute monitoring
                     |
              +------+------+
              |             |
          Recovered     Still active
              |             |
              v             v
           RESOLVED       POLICE
    """

    # ============================================================
    # CONFIGURATION
    # ============================================================

    RIDER_RESPONSE_SECONDS = 30

    # Production default: 30 minutes. Override with NOVASHIELDS_POLICE_ESCALATION_MINUTES for testing.
    try:
        POLICE_ESCALATION_MINUTES = float(
            os.getenv("NOVASHIELDS_POLICE_ESCALATION_MINUTES", "30")
        )
    except ValueError:
        POLICE_ESCALATION_MINUTES = 30.0

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        # Active crash escalation state per device.
        self.active_incidents: Dict[
            str,
            Dict[str, Any]
        ] = {}

    # ============================================================
    # RESOLVE RIDER / PARENT RELATIONSHIP
    # ============================================================

    def resolve_contacts(
        self,
        device_id: str,
        db: Session,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve:

            Device
              ↓
            Vehicle
              ↓
            Rider
              ↓
            Parent
        """

        # --------------------------------------------------------
        # DEVICE -> VEHICLE
        # --------------------------------------------------------

        device_assignment = db.execute(
            select(
                DeviceVehicleAssignment
            ).where(
                DeviceVehicleAssignment.device_id
                == device_id,
                DeviceVehicleAssignment.status
                == "active",
            )
        ).scalar_one_or_none()

        if device_assignment is None:

            print(
                "Emergency escalation:",
                "No active vehicle assignment found."
            )

            return None

        vehicle_id = (
            device_assignment.vehicle_id
        )

        # --------------------------------------------------------
        # VEHICLE -> RIDER
        # --------------------------------------------------------

        vehicle_assignment = db.execute(
            select(
                VehicleRiderAssignment
            ).where(
                VehicleRiderAssignment.vehicle_id
                == vehicle_id,
                VehicleRiderAssignment.status
                == "active",
            )
        ).scalar_one_or_none()

        if vehicle_assignment is None:

            print(
                "Emergency escalation:",
                "No active rider assignment found."
            )

            return None

        rider_id = (
            vehicle_assignment.rider_id
        )

        # --------------------------------------------------------
        # RIDER -> PARENT
        # --------------------------------------------------------

        parent_assignment = db.execute(
            select(
                ParentRiderAssignment
            ).where(
                ParentRiderAssignment.rider_id
                == rider_id,
                ParentRiderAssignment.status
                == "active",
            )
        ).scalar_one_or_none()

        if parent_assignment is None:

            print(
                "Emergency escalation:",
                "No active parent assignment found."
            )

            return None

        parent_id = (
            parent_assignment.parent_id
        )

        return {
            "device_id": device_id,
            "vehicle_id": vehicle_id,
            "rider_id": rider_id,
            "parent_id": parent_id,
        }

    # ============================================================
    # START CRASH ESCALATION
    # ============================================================

    def start_crash(
        self,
        device_id: str,
        crash_event: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Start emergency escalation after crash detection.

        No EmergencyAlert is created here.

        The rider gets 30 seconds to confirm that
        they are safe.
        """

        # --------------------------------------------------------
        # Prevent duplicate escalation
        # --------------------------------------------------------

        if device_id in self.active_incidents:

            return self.get_status(
                device_id
            )

        # --------------------------------------------------------
        # Resolve rider / parent if DB is available
        # --------------------------------------------------------

        contacts = None

        if db is not None:

            contacts = self.resolve_contacts(
                device_id=device_id,
                db=db,
            )

        # --------------------------------------------------------
        # Time
        # --------------------------------------------------------

        now = datetime.now(
            timezone.utc
        )

        cancel_deadline = (
            now
            + timedelta(
                seconds=self.RIDER_RESPONSE_SECONDS
            )
        )

        # --------------------------------------------------------
        # Store incident
        # --------------------------------------------------------

        self.active_incidents[
            device_id
        ] = {

            "device_id": device_id,

            "status":
                "awaiting_rider_response",

            "started_at": now,

            "cancel_deadline":
                cancel_deadline,

            "emergency_started_at":
                None,

            "police_deadline":
                None,

            "rider_cancelled":
                False,

            "parent_notified":
                False,

            "ambulance_notified":
                False,

            "police_notified":
                False,

            "parent_id":
                contacts["parent_id"]
                if contacts
                else crash_event.get(
                    "parent_id"
                ),

            "rider_id":
                contacts["rider_id"]
                if contacts
                else crash_event.get(
                    "rider_id"
                ),

            "vehicle_id":
                contacts["vehicle_id"]
                if contacts
                else crash_event.get(
                    "vehicle_id"
                ),

            "crash_event":
                crash_event,
        }

        print()
        print("=" * 60)
        print(
            "NOVASHIELDS EMERGENCY ESCALATION"
        )
        print("=" * 60)

        print(
            "Crash detected for device:",
            device_id
        )

        print(
            "Rider response deadline:",
            cancel_deadline.isoformat()
        )

        print(
            "Status:",
            "WAITING FOR RIDER"
        )

        print("=" * 60)
        print()

        return self.get_status(
            device_id
        )

    # ============================================================
    # RIDER CONFIRMS THEY ARE OK
    # ============================================================

    def rider_is_ok(
        self,
        device_id: str,
    ) -> Dict[str, Any]:

        incident = (
            self.active_incidents.get(
                device_id
            )
        )

        if incident is None:

            return {
                "success": False,
                "message": (
                    "No active crash escalation "
                    "found."
                ),
            }

        if incident["status"] != (
            "awaiting_rider_response"
        ):

            return {
                "success": False,
                "message": (
                    "The rider response window "
                    "has already ended."
                ),
            }

        incident[
            "rider_cancelled"
        ] = True

        incident[
            "status"
        ] = "cancelled_rider_ok"

        print()
        print("=" * 60)
        print(
            "NOVASHIELDS EMERGENCY CANCELLED"
        )
        print("=" * 60)

        print(
            "Device:",
            device_id
        )

        print(
            "Reason:",
            "Rider confirmed they are OK."
        )

        print("=" * 60)
        print()

        return {
            "success": True,
            **self.get_status(
                device_id
            ),
        }

    # ============================================================
    # CREATE EMERGENCY ALERT
    # ============================================================

    def _create_emergency_alert(
        self,
        db: Session,
        incident: Dict[str, Any],
        alert_type: str,
        severity: str,
        message: str,
    ) -> Optional[EmergencyAlert]:
        """
        Persist an EmergencyAlert in PostgreSQL.
        """

        parent_id = incident.get(
            "parent_id"
        )

        rider_id = incident.get(
            "rider_id"
        )

        vehicle_id = incident.get(
            "vehicle_id"
        )

        device_id = incident.get(
            "device_id"
        )

        crash_event = incident.get(
            "crash_event",
            {}
        )

        incident_id = crash_event.get(
            "incident_id"
        )

        # --------------------------------------------------------
        # Parent/rider relationship is required by DB.
        # --------------------------------------------------------

        if not parent_id:

            print(
                "Emergency alert NOT created:",
                "parent_id missing."
            )

            return None

        if not rider_id:

            print(
                "Emergency alert NOT created:",
                "rider_id missing."
            )

            return None

        # --------------------------------------------------------
        # Create unique alert ID
        # --------------------------------------------------------

        alert_id = (
            "NS-ALERT-"
            + uuid4().hex[:12].upper()
        )

        alert = EmergencyAlert(

            alert_id=alert_id,

            parent_id=parent_id,

            rider_id=rider_id,

            vehicle_id=vehicle_id,

            device_id=device_id,

            incident_id=incident_id,

            alert_type=alert_type,

            severity=severity,

            message=message,

            status="pending",
        )

        db.add(alert)

        try:

            db.commit()

            db.refresh(
                alert
            )

        except Exception as error:

            db.rollback()

            print()
            print("=" * 60)
            print(
                "EMERGENCY ALERT DATABASE ERROR"
            )
            print("=" * 60)

            print(
                "Error:",
                repr(error)
            )

            print("=" * 60)

            return None

        print()
        print("=" * 60)
        print(
            "🚨 EMERGENCY ALERT CREATED"
        )
        print("=" * 60)

        print(
            "Alert ID:",
            alert.alert_id
        )

        print(
            "Type:",
            alert.alert_type
        )

        print(
            "Parent:",
            alert.parent_id
        )

        print(
            "Rider:",
            alert.rider_id
        )

        print(
            "Device:",
            alert.device_id
        )

        print(
            "Incident:",
            alert.incident_id
        )

        print(
            "Severity:",
            alert.severity
        )

        print("=" * 60)
        print()

        return alert

    # ============================================================
    # PROCESS ESCALATION
    # ============================================================

    def process(
        self,
        device_id: str,
        crash_still_active: bool = True,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:

        incident = (
            self.active_incidents.get(
                device_id
            )
        )

        if incident is None:

            return {
                "active": False,
                "action": None,
            }

        now = datetime.now(
            timezone.utc
        )

        # ========================================================
        # RIDER ALREADY CANCELLED
        # ========================================================

        if incident["status"] == (
            "cancelled_rider_ok"
        ):

            return {
                **self.get_status(
                    device_id
                ),
                "action": None,
            }

        # ========================================================
        # 30 SECOND RIDER RESPONSE TIMEOUT
        # ========================================================

        if (
            incident["status"]
            == "awaiting_rider_response"
            and now
            >= incident[
                "cancel_deadline"
            ]
        ):

            incident[
                "status"
            ] = "emergency_escalation"

            incident[
                "emergency_started_at"
            ] = now

            incident[
                "parent_notified"
            ] = True

            incident[
                "ambulance_notified"
            ] = True

            incident[
                "police_deadline"
            ] = (
                now
                + timedelta(
                    minutes=
                    self.POLICE_ESCALATION_MINUTES
                )
            )

            # ----------------------------------------------------
            # CREATE PARENT + AMBULANCE ALERT
            # ----------------------------------------------------

            alert = None

            if db is not None:

                alert = (
                    self._create_emergency_alert(

                        db=db,

                        incident=incident,

                        alert_type=(
                            "crash_emergency"
                        ),

                        severity="critical",

                        message=(
                            "CRITICAL: Possible crash "
                            "detected. Rider did not "
                            "confirm safety within "
                            "30 seconds. Parent and "
                            "emergency medical response "
                            "required."
                        ),
                    )
                )

            print()
            print("=" * 60)
            print(
                "NOVASHIELDS EMERGENCY ESCALATION"
            )
            print("=" * 60)

            print(
                "Device:",
                device_id
            )

            print(
                "30-second rider window expired."
            )

            print(
                "ACTION:",
                "PARENT + AMBULANCE"
            )

            print(
                "Database Alert:",
                "CREATED"
                if alert
                else "NOT CREATED"
            )

            print(
                "Police escalation deadline:",
                incident[
                    "police_deadline"
                ].isoformat()
            )

            print("=" * 60)
            print()

            return {
                **self.get_status(
                    device_id
                ),

                "action": (
                    "notify_parent_and_ambulance"
                ),

                "alert_created": (
                    alert is not None
                ),
            }

        # ========================================================
        # 30 MINUTE POLICE ESCALATION
        # ========================================================

        if (
            incident["status"]
            == "emergency_escalation"

            and incident["police_deadline"]

            and now
            >= incident["police_deadline"]
        ):

            # Prevent duplicate police escalation when process() is called
            # repeatedly after the deadline.
            if incident["police_notified"]:
                return {
                    **self.get_status(device_id),
                    "action": None,
                    "alert_created": False,
                }

            if crash_still_active:

                incident[
                    "status"
                ] = "police_escalation"

                incident[
                    "police_notified"
                ] = True

                # ------------------------------------------------
                # CREATE POLICE ALERT
                # ------------------------------------------------

                alert = None

                if db is not None:

                    alert = (
                        self._create_emergency_alert(

                            db=db,

                            incident=incident,

                            alert_type=(
                                "police_escalation"
                            ),

                            severity="critical",

                            message=(
                                "CRITICAL: Crash emergency "
                                "remains unresolved after "
                                "30 minutes. Police assistance "
                                "required."
                            ),
                        )
                    )

                print()
                print("=" * 60)
                print(
                    "NOVASHIELDS POLICE ESCALATION"
                )
                print("=" * 60)

                print(
                    "Device:",
                    device_id
                )

                print(
                    "Crash condition remains active."
                )

                print(
                    "ACTION:",
                    "POLICE"
                )

                print(
                    "Database Alert:",
                    "CREATED"
                    if alert
                    else "NOT CREATED"
                )

                print("=" * 60)
                print()

                return {
                    **self.get_status(
                        device_id
                    ),

                    "action":
                        "notify_police",

                    "alert_created":
                        alert is not None,
                }

            # ----------------------------------------------------
            # Rider recovered
            # ----------------------------------------------------

            incident[
                "status"
            ] = "resolved"

            return {
                **self.get_status(
                    device_id
                ),

                "action":
                    "close_escalation",
            }

        # ========================================================
        # NO ACTION YET
        # ========================================================

        return {
            **self.get_status(
                device_id
            ),

            "action": None,
        }

    # ============================================================
    # RESOLVE
    # ============================================================

    def resolve(
        self,
        device_id: str,
    ) -> Dict[str, Any]:

        incident = (
            self.active_incidents.get(
                device_id
            )
        )

        if incident is None:

            return {
                "success": False,
                "message": (
                    "No active emergency "
                    "escalation."
                ),
            }

        incident[
            "status"
        ] = "resolved"

        return {
            "success": True,
            **self.get_status(
                device_id
            ),
        }

    # ============================================================
    # GET STATUS
    # ============================================================

    def get_status(
        self,
        device_id: str,
    ) -> Dict[str, Any]:

        incident = (
            self.active_incidents.get(
                device_id
            )
        )

        if incident is None:

            return {
                "active": False,
                "status": "none",
                "device_id": device_id,
            }

        return {

            "active": True,

            "device_id": (
                incident[
                    "device_id"
                ]
            ),

            "status": (
                incident[
                    "status"
                ]
            ),

            "started_at": (
                incident[
                    "started_at"
                ].isoformat()
            ),

            "cancel_deadline": (
                incident[
                    "cancel_deadline"
                ].isoformat()
            ),

            "emergency_started_at": (

                incident[
                    "emergency_started_at"
                ].isoformat()

                if incident[
                    "emergency_started_at"
                ]

                else None
            ),

            "police_deadline": (

                incident[
                    "police_deadline"
                ].isoformat()

                if incident[
                    "police_deadline"
                ]

                else None
            ),

            "rider_cancelled": (
                incident[
                    "rider_cancelled"
                ]
            ),

            "parent_notified": (
                incident[
                    "parent_notified"
                ]
            ),

            "ambulance_notified": (
                incident[
                    "ambulance_notified"
                ]
            ),

            "police_notified": (
                incident[
                    "police_notified"
                ]
            ),

            "parent_id": (
                incident.get(
                    "parent_id"
                )
            ),

            "rider_id": (
                incident.get(
                    "rider_id"
                )
            ),

            "vehicle_id": (
                incident.get(
                    "vehicle_id"
                )
            ),

            "crash_event": (
                incident[
                    "crash_event"
                ]
            ),
        }


# ============================================================
# SINGLE GLOBAL INSTANCE
# ============================================================

emergency_escalation_service = (
    EmergencyEscalationService()
)