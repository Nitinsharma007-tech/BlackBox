from typing import Any, Dict, Optional


class SafetyEventService:
    """
    NovaShields safety-event detection engine.

    Detects only:

        1. Crash
        2. Overspeed
        3. Pothole / vertical impact

    It does NOT detect:

        - Hard braking
        - Aggressive turning

    Crash detection is based primarily on calibrated
    vehicle-angle deviation.

    This service:

        telemetry
             ↓
        event detection
             ↓
        event result

    It does NOT:
        - Store telemetry in the database
        - Manage the Black Box
        - Create emergency alerts
    """

    # ============================================================
    # CONFIGURATION
    # ============================================================

    # ------------------------------------------------------------
    # OVERSPEED
    # ------------------------------------------------------------

    OVERSPEED_LIMIT = 80.0

    # ------------------------------------------------------------
    # POTHOLE / VERTICAL IMPACT
    # ------------------------------------------------------------

    POTHOLE_ACCELERATION_Z = 1.7

    # ------------------------------------------------------------
    # CRASH ANGLE
    # ------------------------------------------------------------

    # Default calibrated crash-angle deviation threshold.
    #
    # Example:
    #
    # Normal calibrated roll  = 0°
    # Current roll             = 50°
    #
    # Roll deviation           = 50°
    #
    # 50 >= 35 → crash
    #
    # This value can later be replaced by a vehicle-specific
    # calibrated threshold.

    CRASH_ANGLE_THRESHOLD = 35.0

    # Optional minimum acceleration confirmation.
    #
    # We don't require extreme acceleration for every crash
    # because a vehicle can fall/tip without producing a huge
    # acceleration spike.

    CRASH_IMPACT_ACCELERATION_Z = 2.5

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        # Previous telemetry packet per device.

        self.previous_telemetry: Dict[
            str,
            Dict[str, Any]
        ] = {}

        # Calibration values per device.

        self.calibration: Dict[
            str,
            Dict[str, float]
        ] = {}

    # ============================================================
    # CALIBRATION
    # ============================================================

    def calibrate_device(
        self,
        device_id: str,
        roll: float,
        pitch: float,
    ) -> Dict[str, float]:
        """
        Store the normal riding angle for a device.

        These values become the baseline.

        Example:

            normal roll  = 2°
            normal pitch = -1°

        Later:

            roll  = 45°
            pitch = 40°

        The service calculates the deviation from the
        calibrated baseline.
        """

        self.calibration[
            device_id
        ] = {

            "roll": float(roll),

            "pitch": float(pitch),
        }

        return self.calibration[
            device_id
        ]

    # ============================================================
    # GET CALIBRATION
    # ============================================================

    def get_calibration(
        self,
        device_id: str,
    ) -> Dict[str, Any]:

        calibration = (
            self.calibration.get(
                device_id
            )
        )

        if calibration is None:

            return {
                "calibrated": False,
                "device_id": device_id,
                "roll": 0.0,
                "pitch": 0.0,
            }

        return {
            "calibrated": True,

            "device_id": device_id,

            "roll": calibration[
                "roll"
            ],

            "pitch": calibration[
                "pitch"
            ],
        }

    # ============================================================
    # MAIN DETECTION FUNCTION
    # ============================================================

    def analyze(
        self,
        telemetry: Dict[str, Any]
    ) -> Dict[str, Any]:

        # ========================================================
        # DEVICE ID
        # ========================================================

        device_id = telemetry.get(
            "device_id"
        )

        if not device_id:

            return {
                "event_detected": False,

                "event_type": None,

                "severity": "unknown",

                "message":
                    "Missing device_id",
            }

        # ========================================================
        # PREVIOUS TELEMETRY
        # ========================================================

        previous = (
            self.previous_telemetry.get(
                device_id
            )
        )

        # ========================================================
        # FIRST PACKET
        # ========================================================

        if previous is None:

            self.previous_telemetry[
                device_id
            ] = telemetry

            return {

                "event_detected": False,

                "event_type": None,

                "severity": "normal",

                "message":
                    "Initial telemetry received",

                "device_id":
                    device_id,
            }

        # ========================================================
        # CURRENT VALUES
        # ========================================================

        speed = float(
            telemetry.get(
                "speed"
            ) or 0
        )

        acceleration_z = float(
            telemetry.get(
                "acceleration_z"
            ) or 0
        )

        roll_raw = float(
            telemetry.get(
                "roll"
            ) or 0
        )

        pitch_raw = float(
            telemetry.get(
                "pitch"
            ) or 0
        )

        # ========================================================
        # CALIBRATION
        # ========================================================

        calibration = (
            self.calibration.get(
                device_id,
                {
                    "roll": 0.0,
                    "pitch": 0.0,
                },
            )
        )

        calibrated_roll = float(
            calibration.get(
                "roll",
                0.0
            )
        )

        calibrated_pitch = float(
            calibration.get(
                "pitch",
                0.0
            )
        )

        # ========================================================
        # ANGLE DEVIATION
        # ========================================================

        roll_deviation = abs(
            roll_raw
            - calibrated_roll
        )

        pitch_deviation = abs(
            pitch_raw
            - calibrated_pitch
        )

        max_angle_deviation = max(
            roll_deviation,
            pitch_deviation,
        )

        # ========================================================
        # PREVIOUS SPEED
        # ========================================================

        previous_speed = float(
            previous.get(
                "speed"
            ) or 0
        )

        speed_drop = (
            previous_speed
            - speed
        )

        # ========================================================
        # EVENT DEFAULT
        # ========================================================

        event_type: Optional[str] = None

        severity = "normal"

        message = "Normal riding"

        # ========================================================
        # EVENT PRIORITY
        # ========================================================
        #
        # 1. CRASH
        # 2. POTHOLE
        # 3. OVERSPEED
        # 4. NORMAL
        #
        # No hard braking.
        # No aggressive turn.
        #
        # ========================================================

        # --------------------------------------------------------
        # 1. CRASH
        # --------------------------------------------------------

        crash_angle_detected = (
            max_angle_deviation
            >= self.CRASH_ANGLE_THRESHOLD
        )

        crash_impact_detected = (
            abs(acceleration_z)
            >= self.CRASH_IMPACT_ACCELERATION_Z
        )

        # A crash can be detected from:
        #
        # A) major angle deviation
        #
        # OR
        #
        # B) major impact combined with meaningful
        #    attitude deviation.
        #
        # This prevents ordinary potholes from becoming crashes.

        crash_detected = (
            crash_angle_detected
            or (
                crash_impact_detected
                and (
                    max_angle_deviation
                    >= 20.0
                )
            )
        )

        if crash_detected:

            event_type = "crash"

            severity = "critical"

            message = (
                "Potential crash detected from "
                "abnormal vehicle angle or impact."
            )

        # --------------------------------------------------------
        # 2. POTHOLE
        # --------------------------------------------------------

        elif (
            abs(acceleration_z)
            >= self.POTHOLE_ACCELERATION_Z
        ):

            event_type = "pothole"

            severity = "medium"

            message = (
                "Potential pothole or vertical "
                "impact detected."
            )

        # --------------------------------------------------------
        # 3. OVERSPEED
        # --------------------------------------------------------

        elif (
            speed
            >= self.OVERSPEED_LIMIT
        ):

            event_type = "overspeed"

            severity = "high"

            message = (
                "Vehicle speed exceeded the "
                "configured 80 km/h safety limit."
            )

        # ========================================================
        # SAVE CURRENT TELEMETRY
        # ========================================================

        self.previous_telemetry[
            device_id
        ] = telemetry

        # ========================================================
        # RETURN RESULT
        # ========================================================

        return {

            "event_detected": (
                event_type is not None
            ),

            "event_type":
                event_type,

            "severity":
                severity,

            "message":
                message,

            "device_id":
                device_id,

            "speed":
                speed,

            "previous_speed":
                previous_speed,

            "speed_drop":
                round(
                    speed_drop,
                    2
                ),

            "acceleration_z":
                acceleration_z,

            "roll":
                roll_raw,

            "pitch":
                pitch_raw,

            "calibrated_roll":
                calibrated_roll,

            "calibrated_pitch":
                calibrated_pitch,

            "roll_deviation":
                round(
                    roll_deviation,
                    2
                ),

            "pitch_deviation":
                round(
                    pitch_deviation,
                    2
                ),

            "max_angle_deviation":
                round(
                    max_angle_deviation,
                    2
                ),

            "crash_angle_detected":
                crash_angle_detected,

            "crash_impact_detected":
                crash_impact_detected,
        }

    # ============================================================
    # RESET DEVICE STATE
    # ============================================================

    def reset_device(
        self,
        device_id: str
    ) -> None:
        """
        Clear telemetry state and calibration
        for a device.
        """

        self.previous_telemetry.pop(
            device_id,
            None
        )

        self.calibration.pop(
            device_id,
            None
        )


# ============================================================
# SINGLE GLOBAL INSTANCE
# ============================================================

safety_event_service = (
    SafetyEventService()
)