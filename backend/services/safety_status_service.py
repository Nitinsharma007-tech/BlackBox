from typing import Any, Dict


class SafetyStatusService:
    """
    NovaShields Guardian Safety Status Service.

    Converts the latest rider telemetry and recent safety events
    into a dashboard-compatible safety status.

    Status levels:

        SAFE
        WARNING
        DANGER
        OFFLINE

    Dashboard compatibility:
        calculate_status(
            device=...,
            latest_telemetry=...,
            recent_incidents=...
        )
    """

    # ============================================================
    # CONFIGURATION
    # ============================================================

    # Speed at or above this value is dangerous.
    OVERSPEED_LIMIT = 80.0

    # Speed at or above this value is considered warning.
    WARNING_SPEED = 60.0

    # Roll / pitch angle indicating a possible crash/fall.
    CRASH_ANGLE = 45.0

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _get_value(
        obj: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Read a value from either:
        - a dictionary
        - a SQLAlchemy model/object
        """

        if obj is None:
            return default

        if isinstance(obj, dict):
            return obj.get(key, default)

        return getattr(obj, key, default)

    # ============================================================
    # MAIN STATUS FUNCTION
    # ============================================================

    def get_status(
        self,
        telemetry: Dict[str, Any] | Any | None = None,
        latest_event: Dict[str, Any] | Any | None = None,
    ) -> Dict[str, Any]:

        # ========================================================
        # NO TELEMETRY
        # ========================================================

        if telemetry is None:
            return {
                "status": "offline",
                "severity": "unknown",
                "message": "No telemetry available.",
                "event_type": None,
            }

        # ========================================================
        # CURRENT TELEMETRY VALUES
        # ========================================================

        speed = float(
            self._get_value(
                telemetry,
                "speed",
                0,
            ) or 0
        )

        roll = abs(
            float(
                self._get_value(
                    telemetry,
                    "roll",
                    0,
                ) or 0
            )
        )

        pitch = abs(
            float(
                self._get_value(
                    telemetry,
                    "pitch",
                    0,
                ) or 0
            )
        )

        # ========================================================
        # LATEST SAFETY EVENT
        # ========================================================

        event_type = self._get_value(
            latest_event,
            "event_type",
            None,
        )

        event_severity = self._get_value(
            latest_event,
            "severity",
            None,
        )

        # Normalize event type.
        if isinstance(event_type, str):
            event_type = event_type.lower().strip()

        # ========================================================
        # DANGER — EXPLICIT CRASH EVENT
        # ========================================================

        if event_type == "crash":

            return {
                "status": "danger",
                "severity": "critical",
                "message": (
                    "Potential crash or vehicle "
                    "fall detected."
                ),
                "event_type": "crash",
            }

        # ========================================================
        # DANGER — ANGLE BASED CRASH DETECTION
        # ========================================================

        if (
            roll >= self.CRASH_ANGLE
            or pitch >= self.CRASH_ANGLE
        ):

            return {
                "status": "danger",
                "severity": "critical",
                "message": (
                    "Vehicle angle indicates "
                    "a possible crash or fall."
                ),
                "event_type": "crash",
            }

        # ========================================================
        # DANGER — EXPLICIT OVERSPEED EVENT
        # ========================================================

        if event_type == "overspeed":

            return {
                "status": "danger",
                "severity": "high",
                "message": (
                    "Vehicle is travelling above "
                    "the configured safety limit."
                ),
                "event_type": "overspeed",
            }

        # ========================================================
        # DANGER — SPEED BASED OVERSPEED
        # ========================================================

        if speed >= self.OVERSPEED_LIMIT:

            return {
                "status": "danger",
                "severity": "high",
                "message": (
                    "Vehicle speed exceeded "
                    "80 km/h."
                ),
                "event_type": "overspeed",
            }

        # ========================================================
        # WARNING — ELEVATED SPEED
        # ========================================================

        if speed >= self.WARNING_SPEED:

            return {
                "status": "at_risk",
                "severity": "medium",
                "message": (
                    "Vehicle speed is elevated."
                ),
                "event_type": None,
            }

        # ========================================================
        # NORMAL
        # ========================================================

        return {
            "status": "safe",
            "severity": "normal",
            "message": "Rider is travelling safely.",
            "event_type": None,
        }

    # ============================================================
    # DASHBOARD COMPATIBILITY FUNCTION
    # ============================================================

    def calculate_status(
        self,
        device: Any = None,
        latest_telemetry: Any = None,
        recent_incidents: list[Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Compatibility method used by the Parent Dashboard.

        The existing dashboard passes SQLAlchemy objects here:

            device
            latest_telemetry
            recent_incidents

        This method converts that input into the format expected
        by get_status().
        """

        # --------------------------------------------------------
        # NO TELEMETRY
        # --------------------------------------------------------

        if latest_telemetry is None:

            return {
                "status": "offline",
                "severity": "unknown",
                "message": "No telemetry available.",
                "event_type": None,
            }

        # --------------------------------------------------------
        # FIND MOST RECENT RELEVANT SAFETY EVENT
        # --------------------------------------------------------

        latest_event = None

        if recent_incidents:

            # recent_incidents are already ordered newest first
            # by the parent dashboard query.

            for incident in recent_incidents:

                incident_type = self._get_value(
                    incident,
                    "event_type",
                    None,
                )

                if isinstance(incident_type, str):
                    incident_type = incident_type.lower().strip()

                # Only events relevant to the current safety
                # status logic are considered.
                if incident_type in {
                    "crash",
                    "overspeed",
                }:
                    latest_event = incident
                    break

        # --------------------------------------------------------
        # CALCULATE STATUS
        # --------------------------------------------------------

        return self.get_status(
            telemetry=latest_telemetry,
            latest_event=latest_event,
        )


# ================================================================
# SINGLE GLOBAL INSTANCE
# ================================================================

safety_status_service = SafetyStatusService()