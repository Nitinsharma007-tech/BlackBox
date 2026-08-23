import argparse
import json
import math
import random
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ============================================================
# NOVASHIELDS VIRTUAL VEHICLE TELEMETRY SIMULATOR
# ============================================================

API_URL = "http://127.0.0.1:8000/api/v1/telemetry"
DEVICE_ID = "NS001"

DEFAULT_INTERVAL = 1.0


# ============================================================
# VIRTUAL BIKE
# ============================================================

class VirtualBike:

    def __init__(self, scenario="normal"):

        # ----------------------------------------------------
        # GPS starting position
        # ----------------------------------------------------

        self.latitude = 29.390000
        self.longitude = 76.970000

        # ----------------------------------------------------
        # Initial speed depends on scenario
        # ----------------------------------------------------

        if scenario == "hard_brake":
            self.speed = 60.0

        elif scenario == "pothole":
            self.speed = 40.0

        elif scenario == "aggressive_turn":
            self.speed = 45.0

        elif scenario == "overspeed":
            self.speed = 80.0

        elif scenario == "crash":
            self.speed = 45.0

        else:
            # Normal scenario starts from parked condition
            self.speed = 0.0

        # ----------------------------------------------------
        # Vehicle orientation
        # ----------------------------------------------------

        self.roll = 0.0
        self.pitch = 0.0

        # ----------------------------------------------------
        # Gyroscope
        # ----------------------------------------------------

        self.gyro_x = 0.0
        self.gyro_y = 0.0
        self.gyro_z = 0.0

        # ----------------------------------------------------
        # Current vehicle state
        # ----------------------------------------------------

        self.state = "PARKED"

        # ----------------------------------------------------
        # Simulation tick
        # ----------------------------------------------------

        self.tick = 0


    # ========================================================
    # NORMAL RIDING
    # ========================================================

    def normal_update(self):

        self.tick += 1

        # ----------------------------------------------------
        # State 1: Starting
        # ----------------------------------------------------

        if self.tick <= 5:

            self.state = "STARTING"

            self.speed += random.uniform(1.5, 3.0)

        # ----------------------------------------------------
        # State 2: Accelerating
        # ----------------------------------------------------

        elif self.tick <= 15:

            self.state = "ACCELERATING"

            self.speed += random.uniform(1.0, 3.0)

        # ----------------------------------------------------
        # State 3: Cruising
        # ----------------------------------------------------

        elif self.tick <= 35:

            self.state = "CRUISING"

            self.speed += random.uniform(-1.5, 1.5)

        # ----------------------------------------------------
        # State 4: Braking
        # ----------------------------------------------------

        elif self.tick <= 42:

            self.state = "BRAKING"

            self.speed -= random.uniform(3.0, 5.0)

        # ----------------------------------------------------
        # State 5: Stopped
        # ----------------------------------------------------

        else:

            self.state = "STOPPED"

            self.speed -= random.uniform(2.0, 4.0)

            if self.speed < 0:
                self.speed = 0.0

        # ----------------------------------------------------
        # Safety limits
        # ----------------------------------------------------

        self.speed = max(0.0, min(self.speed, 70.0))

        # ----------------------------------------------------
        # Normal acceleration
        # ----------------------------------------------------

        acceleration_x = random.uniform(-0.30, 0.30)
        acceleration_y = random.uniform(-0.20, 0.20)
        acceleration_z = random.uniform(0.96, 1.04)

        # ----------------------------------------------------
        # Normal roll
        # ----------------------------------------------------

        self.roll += random.uniform(-0.8, 0.8)

        self.roll = max(
            -12.0,
            min(self.roll, 12.0)
        )

        # ----------------------------------------------------
        # Normal pitch
        # ----------------------------------------------------

        self.pitch += random.uniform(-0.5, 0.5)

        self.pitch = max(
            -7.0,
            min(self.pitch, 7.0)
        )

        # ----------------------------------------------------
        # Normal gyroscope
        # ----------------------------------------------------

        self.gyro_x = random.uniform(-2.5, 2.5)
        self.gyro_y = random.uniform(-2.5, 2.5)
        self.gyro_z = random.uniform(-4.0, 4.0)

        # ----------------------------------------------------
        # GPS movement
        # ----------------------------------------------------

        self.update_gps()

        return (
            acceleration_x,
            acceleration_y,
            acceleration_z
        )


    # ========================================================
    # HARD BRAKING
    # ========================================================

    def hard_brake(self):

        self.tick += 1

        self.state = "HARD_BRAKING"

        # ----------------------------------------------------
        # Rapid reduction in speed
        # ----------------------------------------------------

        self.speed -= random.uniform(7.0, 12.0)

        self.speed = max(
            0.0,
            self.speed
        )

        # ----------------------------------------------------
        # Strong longitudinal braking
        # ----------------------------------------------------

        acceleration_x = random.uniform(
            -2.0,
            -1.2
        )

        acceleration_y = random.uniform(
            -0.4,
            0.4
        )

        acceleration_z = random.uniform(
            0.90,
            1.10
        )

        # ----------------------------------------------------
        # Slight vehicle movement
        # ----------------------------------------------------

        self.roll += random.uniform(
            -2.0,
            2.0
        )

        self.pitch += random.uniform(
            -1.5,
            1.5
        )

        self.roll = max(
            -15.0,
            min(self.roll, 15.0)
        )

        self.pitch = max(
            -10.0,
            min(self.pitch, 10.0)
        )

        # ----------------------------------------------------
        # Increased rotation during braking
        # ----------------------------------------------------

        self.gyro_x = random.uniform(
            -8.0,
            8.0
        )

        self.gyro_y = random.uniform(
            -8.0,
            8.0
        )

        self.gyro_z = random.uniform(
            -12.0,
            12.0
        )

        self.update_gps()

        return (
            acceleration_x,
            acceleration_y,
            acceleration_z
        )


    # ========================================================
    # OVERSPEED
    # ========================================================

    def overspeed(self):

        self.tick += 1

        self.state = "OVERSPEED"

        # ----------------------------------------------------
        # Increase speed gradually
        # ----------------------------------------------------

        self.speed += random.uniform(
            2.0,
            4.0
        )

        self.speed = min(
            self.speed,
            110.0
        )

        # ----------------------------------------------------
        # Moderate acceleration
        # ----------------------------------------------------

        acceleration_x = random.uniform(
            -0.5,
            0.5
        )

        acceleration_y = random.uniform(
            -0.4,
            0.4
        )

        acceleration_z = random.uniform(
            0.95,
            1.05
        )

        # ----------------------------------------------------
        # Slight orientation variation
        # ----------------------------------------------------

        self.roll += random.uniform(
            -1.0,
            1.0
        )

        self.pitch += random.uniform(
            -0.5,
            0.5
        )

        self.roll = max(
            -15.0,
            min(self.roll, 15.0)
        )

        self.pitch = max(
            -8.0,
            min(self.pitch, 8.0)
        )

        # ----------------------------------------------------
        # Gyroscope
        # ----------------------------------------------------

        self.gyro_x = random.uniform(
            -4.0,
            4.0
        )

        self.gyro_y = random.uniform(
            -4.0,
            4.0
        )

        self.gyro_z = random.uniform(
            -7.0,
            7.0
        )

        self.update_gps()

        return (
            acceleration_x,
            acceleration_y,
            acceleration_z
        )


    # ========================================================
    # AGGRESSIVE TURN
    # ========================================================

    def aggressive_turn(self):

        self.tick += 1

        self.state = "AGGRESSIVE_TURN"

        # ----------------------------------------------------
        # Maintain meaningful riding speed
        # ----------------------------------------------------

        self.speed += random.uniform(
            -1.0,
            1.0
        )

        self.speed = max(
            45.0,
            self.speed
        )

        self.speed = min(
            65.0,
            self.speed
        )

        # ----------------------------------------------------
        # Lateral acceleration
        # ----------------------------------------------------

        acceleration_x = random.uniform(
            -0.8,
            0.8
        )

        acceleration_y = random.uniform(
            -1.5,
            1.5
        )

        acceleration_z = random.uniform(
            0.90,
            1.10
        )

        # ----------------------------------------------------
        # Strong lean
        # ----------------------------------------------------

        self.roll += random.choice([
            random.uniform(4.0, 8.0),
            random.uniform(-8.0, -4.0)
        ])

        self.roll = max(
            -35.0,
            min(self.roll, 35.0)
        )

        self.pitch += random.uniform(
            -2.0,
            2.0
        )

        self.pitch = max(
            -12.0,
            min(self.pitch, 12.0)
        )

        # ----------------------------------------------------
        # High angular velocity
        # ----------------------------------------------------

        self.gyro_x = random.uniform(
            -15.0,
            15.0
        )

        self.gyro_y = random.uniform(
            -15.0,
            15.0
        )

        self.gyro_z = random.uniform(
            -25.0,
            25.0
        )

        self.update_gps()

        return (
            acceleration_x,
            acceleration_y,
            acceleration_z
        )


    # ========================================================
    # POTHOLE
    # ========================================================

    def pothole(self):

        self.tick += 1

        self.state = "POTHOLE"

        # ----------------------------------------------------
        # Vehicle continues moving
        # ----------------------------------------------------

        self.speed += random.uniform(
            -2.0,
            1.0
        )

        self.speed = max(
            25.0,
            self.speed
        )

        # ----------------------------------------------------
        # Normal horizontal movement
        # ----------------------------------------------------

        acceleration_x = random.uniform(
            -0.8,
            0.8
        )

        acceleration_y = random.uniform(
            -0.8,
            0.8
        )

        # ----------------------------------------------------
        # Strong short vertical impact
        # ----------------------------------------------------

        acceleration_z = random.uniform(
            1.8,
            2.5
        )

        # ----------------------------------------------------
        # Temporary orientation disturbance
        # ----------------------------------------------------

        self.roll += random.uniform(
            -3.0,
            3.0
        )

        self.pitch += random.uniform(
            -2.0,
            2.0
        )

        self.roll = max(
            -20.0,
            min(self.roll, 20.0)
        )

        self.pitch = max(
            -12.0,
            min(self.pitch, 12.0)
        )

        # ----------------------------------------------------
        # Short rotational shock
        # ----------------------------------------------------

        self.gyro_x = random.uniform(
            -10.0,
            10.0
        )

        self.gyro_y = random.uniform(
            -10.0,
            10.0
        )

        self.gyro_z = random.uniform(
            -15.0,
            15.0
        )

        self.update_gps()

        return (
            acceleration_x,
            acceleration_y,
            acceleration_z
        )


    # ========================================================
    # CRASH
    # ========================================================

    def crash(self):

        self.tick += 1

        self.state = "CRASH"

        # ----------------------------------------------------
        # Maintain impact speed
        # ----------------------------------------------------

        self.speed = random.uniform(
            35.0,
            55.0
        )

        # ----------------------------------------------------
        # Severe impact acceleration
        # ----------------------------------------------------

        acceleration_x = random.uniform(
            -5.0,
            -3.5
        )

        acceleration_y = random.uniform(
            -2.0,
            2.0
        )

        acceleration_z = random.uniform(
            2.5,
            4.5
        )

        # ----------------------------------------------------
        # Abnormal orientation
        # ----------------------------------------------------

        self.roll = random.choice([
            random.uniform(55.0, 85.0),
            random.uniform(-85.0, -55.0)
        ])

        self.pitch = random.choice([
            random.uniform(35.0, 60.0),
            random.uniform(-60.0, -35.0)
        ])

        # ----------------------------------------------------
        # Severe angular velocity
        # ----------------------------------------------------

        self.gyro_x = random.uniform(
            -40.0,
            40.0
        )

        self.gyro_y = random.uniform(
            -40.0,
            40.0
        )

        self.gyro_z = random.uniform(
            -60.0,
            60.0
        )

        self.update_gps()

        return (
            acceleration_x,
            acceleration_y,
            acceleration_z
        )


    # ========================================================
    # GPS MOVEMENT
    # ========================================================

    def update_gps(self):

        if self.speed <= 0:
            return

        # ----------------------------------------------------
        # Random heading
        # ----------------------------------------------------

        heading = random.uniform(
            0,
            2 * math.pi
        )

        # ----------------------------------------------------
        # Approximate movement
        # ----------------------------------------------------

        movement = self.speed * 0.000002

        self.latitude += (
            math.cos(heading) * movement
        )

        self.longitude += (
            math.sin(heading) * movement
        )


    # ========================================================
    # GENERATE TELEMETRY
    # ========================================================

    def generate(self, scenario):

        if scenario == "normal":

            ax, ay, az = self.normal_update()

        elif scenario == "hard_brake":

            ax, ay, az = self.hard_brake()

        elif scenario == "overspeed":

            ax, ay, az = self.overspeed()

        elif scenario == "aggressive_turn":

            ax, ay, az = self.aggressive_turn()

        elif scenario == "pothole":

            ax, ay, az = self.pothole()

        elif scenario == "crash":

            ax, ay, az = self.crash()

        else:

            raise ValueError(
                f"Unknown scenario: {scenario}"
            )

        # ----------------------------------------------------
        # Final telemetry packet
        # ----------------------------------------------------

        return {

            "device_id": DEVICE_ID,

            "timestamp": (
                datetime.now(timezone.utc)
                .isoformat()
            ),

            "latitude": round(
                self.latitude,
                6
            ),

            "longitude": round(
                self.longitude,
                6
            ),

            "speed": round(
                self.speed,
                2
            ),

            "acceleration_x": round(
                ax,
                3
            ),

            "acceleration_y": round(
                ay,
                3
            ),

            "acceleration_z": round(
                az,
                3
            ),

            "gyro_x": round(
                self.gyro_x,
                3
            ),

            "gyro_y": round(
                self.gyro_y,
                3
            ),

            "gyro_z": round(
                self.gyro_z,
                3
            ),

            "roll": round(
                self.roll,
                2
            ),

            "pitch": round(
                self.pitch,
                2
            )
        }


# ============================================================
# SEND TELEMETRY TO FASTAPI
# ============================================================

def send_telemetry(telemetry):

    data = json.dumps(
        telemetry
    ).encode("utf-8")

    request = Request(

        API_URL,

        data=data,

        headers={
            "Content-Type": "application/json"
        },

        method="POST"
    )

    try:

        with urlopen(
            request,
            timeout=5
        ) as response:

            response_data = (
                response
                .read()
                .decode("utf-8")
            )

            return True, response_data

    except HTTPError as error:

        try:
            body = (
                error
                .read()
                .decode("utf-8")
            )

        except Exception:
            body = ""

        return False, (
            f"HTTP {error.code}: {body}"
        )

    except URLError as error:

        return False, (
            f"Connection error: "
            f"{error.reason}"
        )

    except Exception as error:

        return False, str(error)


# ============================================================
# MAIN SIMULATOR
# ============================================================

def main():

    # --------------------------------------------------------
    # Command-line arguments
    # --------------------------------------------------------

    parser = argparse.ArgumentParser(

        description=(
            "NovaShields Virtual Vehicle "
            "Telemetry Simulator"
        )
    )

    parser.add_argument(

        "--scenario",

        choices=[
            "normal",
            "hard_brake",
            "overspeed",
            "aggressive_turn",
            "pothole",
            "crash"
        ],

        default="normal",

        help=(
            "Telemetry scenario to simulate"
        )
    )

    parser.add_argument(

        "--interval",

        type=float,

        default=DEFAULT_INTERVAL,

        help=(
            "Seconds between telemetry packets"
        )
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Validate interval
    # --------------------------------------------------------

    if args.interval <= 0:

        print(
            "ERROR: Interval must be greater than 0."
        )

        return

    # --------------------------------------------------------
    # Create virtual bike
    # --------------------------------------------------------

    bike = VirtualBike(
        args.scenario
    )

    # --------------------------------------------------------
    # Startup information
    # --------------------------------------------------------

    print()

    print("=" * 70)

    print(
        "             NOVASHIELDS VIRTUAL VEHICLE"
    )

    print("=" * 70)

    print()

    print(
        f"Device ID : {DEVICE_ID}"
    )

    print(
        f"Scenario  : {args.scenario}"
    )

    print(
        f"API       : {API_URL}"
    )

    print(
        f"Interval  : {args.interval}s"
    )

    print()

    print(
        "Press CTRL+C to stop."
    )

    print()

    counter = 0

    # --------------------------------------------------------
    # Continuous telemetry loop
    # --------------------------------------------------------

    try:

        while True:

            telemetry = bike.generate(
                args.scenario
            )

            success, response = (
                send_telemetry(
                    telemetry
                )
            )

            counter += 1

            if success:

                print(

                    f"[{counter:04d}] "
                    f"✓ "

                    f"{bike.state:<16} | "

                    f"Speed: "
                    f"{telemetry['speed']:>6.2f} | "

                    f"Roll: "
                    f"{telemetry['roll']:>7.2f} | "

                    f"Pitch: "
                    f"{telemetry['pitch']:>7.2f} | "

                    f"Accel-Z: "
                    f"{telemetry['acceleration_z']:>5.2f}"

                )

            else:

                print(

                    f"[{counter:04d}] "
                    f"✗ Failed | "
                    f"{response}"

                )

            time.sleep(
                args.interval
            )

    except KeyboardInterrupt:

        print()

        print("=" * 70)

        print(
            "Simulator stopped."
        )

        print(
            f"Packets generated: {counter}"
        )

        print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()