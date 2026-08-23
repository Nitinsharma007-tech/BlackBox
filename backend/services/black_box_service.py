from collections import deque
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional


# ============================================================
# NOVASHIELDS — 30 SECOND ROLLING BLACK BOX
# ============================================================
#
# Purpose:
# Maintain the latest 30 seconds of telemetry for each device.
#
# Important:
# - This is NOT the permanent database.
# - PostgreSQL continues storing all telemetry.
# - This service maintains a real-time working window.
# - Later, the buffer will be frozen when a crash is detected.
#
# Flow:
#
# Telemetry
#     ↓
# BlackBoxService
#     ↓
# Latest 30 seconds
#     ↓
# Crash detected
#     ↓
# Freeze buffer
#
# ============================================================


class BlackBoxService:
    """
    Real-time rolling black box for NovaShields.

    Each device gets its own telemetry buffer.

    Example:

        NS001 -> last 30 seconds
        NS002 -> last 30 seconds
        NS003 -> last 30 seconds

    The service is thread-safe because FastAPI can process
    multiple requests concurrently.
    """

    def __init__(self, window_seconds: int = 30):

        # ----------------------------------------------------
        # Configuration
        # ----------------------------------------------------

        self.window_seconds = window_seconds

        # ----------------------------------------------------
        # Device buffers
        #
        # {
        #     "NS001": deque([...]),
        #     "NS002": deque([...])
        # }
        # ----------------------------------------------------

        self.buffers: Dict[str, deque] = {}

        # ----------------------------------------------------
        # Frozen buffers
        #
        # When a crash/event is detected later, the current
        # rolling buffer can be frozen here.
        # ----------------------------------------------------

        self.frozen_buffers: Dict[str, List[Dict[str, Any]]] = {}

        # ----------------------------------------------------
        # Device freeze status
        # ----------------------------------------------------

        self.frozen_devices = set()

        # ----------------------------------------------------
        # Thread safety
        # ----------------------------------------------------

        self.lock = Lock()


    # ========================================================
    # INTERNAL — GET OR CREATE DEVICE BUFFER
    # ========================================================

    def _get_buffer(self, device_id: str) -> deque:

        if device_id not in self.buffers:

            self.buffers[device_id] = deque()

        return self.buffers[device_id]


    # ========================================================
    # ADD TELEMETRY
    # ========================================================

    def add_telemetry(
        self,
        telemetry: Dict[str, Any]
    ) -> Dict[str, Any]:

        """
        Add one telemetry packet to the rolling buffer.

        Expected telemetry:

        {
            "device_id": "NS001",
            "timestamp": "...",
            "latitude": ...,
            "longitude": ...,
            "speed": ...,
            "acceleration_x": ...,
            "acceleration_y": ...,
            "acceleration_z": ...,
            "gyro_x": ...,
            "gyro_y": ...,
            "gyro_z": ...,
            "roll": ...,
            "pitch": ...
        }

        Returns information about the current buffer.
        """

        # ----------------------------------------------------
        # Validate device ID
        # ----------------------------------------------------

        device_id = telemetry.get("device_id")

        if not device_id:

            raise ValueError(
                "Telemetry must contain device_id"
            )

        with self.lock:

            # ------------------------------------------------
            # If device is frozen, don't modify its evidence
            # ------------------------------------------------

            if device_id in self.frozen_devices:

                return {
                    "status": "frozen",
                    "device_id": device_id,
                    "message": (
                        "Black box is frozen for this device."
                    )
                }

            # ------------------------------------------------
            # Get device buffer
            # ------------------------------------------------

            buffer = self._get_buffer(device_id)

            # ------------------------------------------------
            # Add telemetry
            # ------------------------------------------------

            buffer.append(telemetry)

            # ------------------------------------------------
            # Remove telemetry older than the 30-second window
            # ------------------------------------------------

            self._cleanup_buffer(
                device_id
            )

            # ------------------------------------------------
            # Return current state
            # ------------------------------------------------

            return self._get_buffer_status(
                device_id
            )


    # ========================================================
    # REMOVE OLD TELEMETRY
    # ========================================================

    def _cleanup_buffer(
        self,
        device_id: str
    ) -> None:

        """
        Keep only telemetry inside the configured time window.
        """

        buffer = self._get_buffer(
            device_id
        )

        if not buffer:
            return

        # ----------------------------------------------------
        # Get newest telemetry timestamp
        # ----------------------------------------------------

        newest_timestamp = self._parse_timestamp(
            buffer[-1].get("timestamp")
        )

        if newest_timestamp is None:
            return

        # ----------------------------------------------------
        # Calculate cutoff
        # ----------------------------------------------------

        cutoff = (
            newest_timestamp
            - timedelta(
                seconds=self.window_seconds
            )
        )

        # ----------------------------------------------------
        # Remove old packets
        # ----------------------------------------------------

        while buffer:

            oldest_timestamp = self._parse_timestamp(
                buffer[0].get("timestamp")
            )

            # If timestamp cannot be parsed, keep it for now
            if oldest_timestamp is None:
                break

            if oldest_timestamp < cutoff:

                buffer.popleft()

            else:

                break


    # ========================================================
    # PARSE TIMESTAMP
    # ========================================================

    @staticmethod
    def _parse_timestamp(
        timestamp: Optional[str]
    ) -> Optional[datetime]:

        if not timestamp:
            return None

        try:

            value = datetime.fromisoformat(
                timestamp.replace(
                    "Z",
                    "+00:00"
                )
            )

            # ------------------------------------------------
            # Ensure timezone-aware datetime
            # ------------------------------------------------

            if value.tzinfo is None:

                value = value.replace(
                    tzinfo=timezone.utc
                )

            return value

        except (
            ValueError,
            TypeError
        ):

            return None


    # ========================================================
    # GET CURRENT BUFFER
    # ========================================================

    def get_buffer(
        self,
        device_id: str
    ) -> List[Dict[str, Any]]:

        """
        Return the current rolling telemetry buffer.
        """

        with self.lock:

            buffer = self._get_buffer(
                device_id
            )

            return list(buffer)


    # ========================================================
    # GET BUFFER STATUS
    # ========================================================

    def _get_buffer_status(
        self,
        device_id: str
    ) -> Dict[str, Any]:

        buffer = self._get_buffer(
            device_id
        )

        if not buffer:

            return {
                "status": "empty",
                "device_id": device_id,
                "window_seconds": self.window_seconds,
                "record_count": 0,
                "oldest_timestamp": None,
                "newest_timestamp": None,
                "duration_seconds": 0,
                "is_frozen": (
                    device_id in self.frozen_devices
                )
    }

        oldest_timestamp = (
            buffer[0].get("timestamp")
        )

        newest_timestamp = (
            buffer[-1].get("timestamp")
        )

        # ----------------------------------------------------
        # Calculate actual duration
        # ----------------------------------------------------

        oldest_dt = self._parse_timestamp(
            oldest_timestamp
        )

        newest_dt = self._parse_timestamp(
            newest_timestamp
        )

        duration_seconds = 0.0

        if oldest_dt and newest_dt:

            duration_seconds = (
                newest_dt - oldest_dt
            ).total_seconds()

        return {

            "status": "active",

            "device_id": device_id,

            "window_seconds": (
                self.window_seconds
            ),

            "record_count": len(buffer),

            "oldest_timestamp": (
                oldest_timestamp
            ),

            "newest_timestamp": (
                newest_timestamp
            ),

            "duration_seconds": round(
                duration_seconds,
                2
            ),

            "is_frozen": (
                device_id
                in self.frozen_devices
            )
        }


    # ========================================================
    # PUBLIC — BUFFER STATUS
    # ========================================================

    def get_status(
        self,
        device_id: str
    ) -> Dict[str, Any]:

        """
        Get information about the current black box.
        """

        with self.lock:

            return self._get_buffer_status(
                device_id
            )


    # ========================================================
    # FREEZE BLACK BOX
    # ========================================================

    def freeze(
        self,
        device_id: str
    ) -> Dict[str, Any]:

        """
        Freeze the current rolling buffer.

        This will later be called when the crash detection
        engine confirms a crash.

        The frozen data becomes the evidence snapshot.
        """

        with self.lock:

            # ------------------------------------------------
            # Get current buffer
            # ------------------------------------------------

            buffer = self._get_buffer(
                device_id
            )

            # ------------------------------------------------
            # Copy the buffer
            #
            # IMPORTANT:
            # We copy it instead of referencing the deque.
            # ------------------------------------------------

            frozen_data = list(
                buffer
            )

            # ------------------------------------------------
            # Store frozen evidence
            # ------------------------------------------------

            self.frozen_buffers[
                device_id
            ] = frozen_data

            # ------------------------------------------------
            # Mark device as frozen
            # ------------------------------------------------

            self.frozen_devices.add(
                device_id
            )

            return {

                "status": "frozen",

                "device_id": device_id,

                "record_count": len(
                    frozen_data
                ),

                "oldest_timestamp": (
                    frozen_data[0].get("timestamp")
                    if frozen_data
                    else None
                ),

                "newest_timestamp": (
                    frozen_data[-1].get("timestamp")
                    if frozen_data
                    else None
                )
            }


    # ========================================================
    # GET FROZEN EVIDENCE
    # ========================================================

    def get_frozen_evidence(
        self,
        device_id: str
    ) -> List[Dict[str, Any]]:

        """
        Return the frozen evidence for a device.
        """

        with self.lock:

            return list(
                self.frozen_buffers.get(
                    device_id,
                    []
                )
            )


    # ========================================================
    # UNFREEZE / RESET
    # ========================================================

    def reset(
        self,
        device_id: str
    ) -> Dict[str, Any]:

        """
        Reset a device's black box.

        This will be useful after an incident has been
        processed and the device returns to normal operation.
        """

        with self.lock:

            # ------------------------------------------------
            # Remove frozen state
            # ------------------------------------------------

            self.frozen_devices.discard(
                device_id
            )

            # ------------------------------------------------
            # Remove frozen evidence
            # ------------------------------------------------

            self.frozen_buffers.pop(
                device_id,
                None
            )

            # ------------------------------------------------
            # Clear current rolling buffer
            # ------------------------------------------------

            self.buffers.pop(
                device_id,
                None
            )

            return {

                "status": "reset",

                "device_id": device_id,

                "message": (
                    "Black box reset successfully."
                )
            }


# ============================================================
# SINGLE GLOBAL BLACK BOX INSTANCE
# ============================================================
#
# FastAPI will use this same instance so the rolling buffer
# remains available between telemetry requests.
#
# ============================================================

black_box_service = BlackBoxService(
    window_seconds=30
)