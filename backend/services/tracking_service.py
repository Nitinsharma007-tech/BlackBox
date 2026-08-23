from datetime import datetime, timezone


class TrackingService:

    # Telemetry is considered online if it is
    # received within the last 30 seconds.
    ONLINE_THRESHOLD_SECONDS = 30

    @staticmethod
    def get_tracking_status(
        timestamp,
        now=None,
    ):

        if timestamp is None:
            return "offline"

        if now is None:
            now = datetime.now(timezone.utc)

        # Ensure timezone compatibility
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        age_seconds = (
            now - timestamp
        ).total_seconds()

        if age_seconds <= TrackingService.ONLINE_THRESHOLD_SECONDS:
            return "online"

        return "offline"


tracking_service = TrackingService()