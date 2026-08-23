from datetime import datetime, timedelta, timezone

from backend.services.black_box_service import BlackBoxService


# ============================================================
# NOVASHIELDS BLACK BOX TEST
# ============================================================
#
# This test verifies:
#
# 1. Telemetry can be added
# 2. Multiple devices have separate buffers
# 3. Old telemetry is removed
# 4. Only the latest 30 seconds remain
# 5. Buffer status is correct
# 6. Black box can be frozen
# 7. Frozen evidence remains available
# 8. Black box can be reset
#
# ============================================================


def create_telemetry(
    device_id: str,
    timestamp: datetime,
    speed: float
):
    """
    Create a small synthetic telemetry packet.

    We don't need every real sensor field for this
    unit test because we're testing the Black Box,
    not the telemetry API.
    """

    return {
        "device_id": device_id,

        "timestamp": timestamp.isoformat(),

        "latitude": 29.390000,

        "longitude": 76.970000,

        "speed": speed,

        "acceleration_x": 0.10,

        "acceleration_y": 0.05,

        "acceleration_z": 1.00,

        "gyro_x": 0.20,

        "gyro_y": 0.10,

        "gyro_z": 0.30,

        "roll": 2.0,

        "pitch": 1.0
    }


# ============================================================
# TEST 1 — BASIC ADDITION
# ============================================================

def test_add_telemetry():

    service = BlackBoxService(
        window_seconds=30
    )

    start_time = datetime.now(
        timezone.utc
    )

    telemetry = create_telemetry(
        device_id="NS001",
        timestamp=start_time,
        speed=40.0
    )

    result = service.add_telemetry(
        telemetry
    )

    assert result["status"] == "active"

    assert result["device_id"] == "NS001"

    assert result["record_count"] == 1

    print(
        "✓ TEST 1 PASSED — "
        "Telemetry added successfully"
    )


# ============================================================
# TEST 2 — ROLLING WINDOW
# ============================================================

def test_rolling_window():

    service = BlackBoxService(
        window_seconds=30
    )

    start_time = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Add telemetry every second from 0 to 40 seconds
    # --------------------------------------------------------

    for second in range(41):

        timestamp = (
            start_time
            + timedelta(seconds=second)
        )

        telemetry = create_telemetry(
            device_id="NS001",
            timestamp=timestamp,
            speed=30.0 + second
        )

        service.add_telemetry(
            telemetry
        )

    # --------------------------------------------------------
    # Get current buffer
    # --------------------------------------------------------

    buffer = service.get_buffer(
        "NS001"
    )

    # --------------------------------------------------------
    # The buffer should contain roughly the latest
    # 30 seconds.
    #
    # At t=40:
    #
    # cutoff = t=10
    #
    # Therefore t=10 through t=40 remain.
    #
    # That's 31 records because both endpoints are included.
    # --------------------------------------------------------

    assert len(buffer) == 31

    # --------------------------------------------------------
    # Oldest should be t=10
    # --------------------------------------------------------

    oldest = service._parse_timestamp(
        buffer[0]["timestamp"]
    )

    expected_oldest = (
        start_time
        + timedelta(seconds=10)
    )

    assert oldest == expected_oldest

    # --------------------------------------------------------
    # Newest should be t=40
    # --------------------------------------------------------

    newest = service._parse_timestamp(
        buffer[-1]["timestamp"]
    )

    expected_newest = (
        start_time
        + timedelta(seconds=40)
    )

    assert newest == expected_newest

    print(
        "✓ TEST 2 PASSED — "
        "30-second rolling window works"
    )


# ============================================================
# TEST 3 — BUFFER STATUS
# ============================================================

def test_buffer_status():

    service = BlackBoxService(
        window_seconds=30
    )

    start_time = datetime.now(
        timezone.utc
    )

    for second in range(11):

        timestamp = (
            start_time
            + timedelta(seconds=second)
        )

        telemetry = create_telemetry(
            device_id="NS001",
            timestamp=timestamp,
            speed=40.0
        )

        service.add_telemetry(
            telemetry
        )

    status = service.get_status(
        "NS001"
    )

    assert status["status"] == "active"

    assert status["device_id"] == "NS001"

    assert status["record_count"] == 11

    assert status["duration_seconds"] == 10.0

    assert status["is_frozen"] is False

    print(
        "✓ TEST 3 PASSED — "
        "Buffer status is correct"
    )


# ============================================================
# TEST 4 — MULTIPLE DEVICES
# ============================================================

def test_multiple_devices():

    service = BlackBoxService(
        window_seconds=30
    )

    start_time = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Device NS001
    # --------------------------------------------------------

    for second in range(5):

        telemetry = create_telemetry(
            device_id="NS001",

            timestamp=(
                start_time
                + timedelta(seconds=second)
            ),

            speed=40.0
        )

        service.add_telemetry(
            telemetry
        )

    # --------------------------------------------------------
    # Device NS002
    # --------------------------------------------------------

    for second in range(8):

        telemetry = create_telemetry(
            device_id="NS002",

            timestamp=(
                start_time
                + timedelta(seconds=second)
            ),

            speed=50.0
        )

        service.add_telemetry(
            telemetry
        )

    # --------------------------------------------------------
    # Check buffers independently
    # --------------------------------------------------------

    buffer_1 = service.get_buffer(
        "NS001"
    )

    buffer_2 = service.get_buffer(
        "NS002"
    )

    assert len(buffer_1) == 5

    assert len(buffer_2) == 8

    assert all(
        item["device_id"] == "NS001"
        for item in buffer_1
    )

    assert all(
        item["device_id"] == "NS002"
        for item in buffer_2
    )

    print(
        "✓ TEST 4 PASSED — "
        "Multiple device buffers work independently"
    )


# ============================================================
# TEST 5 — FREEZE BLACK BOX
# ============================================================

def test_freeze():

    service = BlackBoxService(
        window_seconds=30
    )

    start_time = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Add telemetry
    # --------------------------------------------------------

    for second in range(10):

        telemetry = create_telemetry(
            device_id="NS001",

            timestamp=(
                start_time
                + timedelta(seconds=second)
            ),

            speed=40.0 + second
        )

        service.add_telemetry(
            telemetry
        )

    # --------------------------------------------------------
    # Freeze
    # --------------------------------------------------------

    result = service.freeze(
        "NS001"
    )

    assert result["status"] == "frozen"

    assert result["device_id"] == "NS001"

    assert result["record_count"] == 10

    # --------------------------------------------------------
    # Verify evidence
    # --------------------------------------------------------

    evidence = service.get_frozen_evidence(
        "NS001"
    )

    assert len(evidence) == 10

    assert evidence[0]["speed"] == 40.0

    assert evidence[-1]["speed"] == 49.0

    print(
        "✓ TEST 5 PASSED — "
        "Black box freeze works"
    )


# ============================================================
# TEST 6 — FROZEN BUFFER DOES NOT CHANGE
# ============================================================

def test_frozen_buffer():

    service = BlackBoxService(
        window_seconds=30
    )

    start_time = datetime.now(
        timezone.utc
    )

    # --------------------------------------------------------
    # Initial telemetry
    # --------------------------------------------------------

    for second in range(5):

        telemetry = create_telemetry(
            device_id="NS001",

            timestamp=(
                start_time
                + timedelta(seconds=second)
            ),

            speed=40.0
        )

        service.add_telemetry(
            telemetry
        )

    # --------------------------------------------------------
    # Freeze
    # --------------------------------------------------------

    service.freeze(
        "NS001"
    )

    # --------------------------------------------------------
    # Try adding new telemetry after freeze
    # --------------------------------------------------------

    new_telemetry = create_telemetry(
        device_id="NS001",

        timestamp=(
            start_time
            + timedelta(seconds=10)
        ),

        speed=100.0
    )

    result = service.add_telemetry(
        new_telemetry
    )

    # --------------------------------------------------------
    # Service should report frozen
    # --------------------------------------------------------

    assert result["status"] == "frozen"

    # --------------------------------------------------------
    # Evidence should still contain only original records
    # --------------------------------------------------------

    evidence = service.get_frozen_evidence(
        "NS001"
    )

    assert len(evidence) == 5

    assert evidence[-1]["speed"] == 40.0

    print(
        "✓ TEST 6 PASSED — "
        "Frozen evidence is protected"
    )


# ============================================================
# TEST 7 — RESET
# ============================================================

def test_reset():

    service = BlackBoxService(
        window_seconds=30
    )

    start_time = datetime.now(
        timezone.utc
    )

    telemetry = create_telemetry(
        device_id="NS001",
        timestamp=start_time,
        speed=40.0
    )

    service.add_telemetry(
        telemetry
    )

    # --------------------------------------------------------
    # Freeze first
    # --------------------------------------------------------

    service.freeze(
        "NS001"
    )

    # --------------------------------------------------------
    # Reset
    # --------------------------------------------------------

    result = service.reset(
        "NS001"
    )

    assert result["status"] == "reset"

    # --------------------------------------------------------
    # Buffer should be empty
    # --------------------------------------------------------

    buffer = service.get_buffer(
        "NS001"
    )

    assert len(buffer) == 0

    # --------------------------------------------------------
    # Evidence should also be removed
    # --------------------------------------------------------

    evidence = service.get_frozen_evidence(
        "NS001"
    )

    assert len(evidence) == 0

    # --------------------------------------------------------
    # Device should no longer be frozen
    # --------------------------------------------------------

    status = service.get_status(
        "NS001"
    )

    assert status["is_frozen"] is False

    print(
        "✓ TEST 7 PASSED — "
        "Black box reset works"
    )


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("        NOVASHIELDS BLACK BOX TEST SUITE")
    print("=" * 70)
    print()

    test_add_telemetry()

    test_rolling_window()

    test_buffer_status()

    test_multiple_devices()

    test_freeze()

    test_frozen_buffer()

    test_reset()

    print()
    print("=" * 70)
    print("        ALL BLACK BOX TESTS PASSED")
    print("=" * 70)
    print()