const APP = "rider";

// ============================================================
// AUTHENTICATION
// ============================================================

const token = NovaAPI.getToken(APP);

if (!token) {
    window.location.href = "../login/index.html";
}

const user = NovaAPI.getUser(APP);
const profile = NovaAPI.getProfile(APP);

// ============================================================
// UI ELEMENTS
// ============================================================

const riderGreeting = document.getElementById("riderGreeting");

const gpsStatus = document.getElementById("gpsStatus");
const gpsIndicator = document.getElementById("gpsIndicator");

const safetyStatus = document.getElementById("safetyStatus");
const safetyIcon = document.getElementById("safetyIcon");

const currentSpeed = document.getElementById("currentSpeed");
const speedProgress = document.getElementById("speedProgress");

const leanAngle = document.getElementById("leanAngle");
const leanStatus = document.getElementById("leanStatus");

const accelerationValue = document.getElementById("accelerationValue");
const accelerationStatus = document.getElementById(
    "accelerationStatus"
);

const rideTime = document.getElementById("rideTime");
const rideDistance = document.getElementById("rideDistance");

const emergencyButton = document.getElementById(
    "emergencyButton"
);

// ============================================================
// USER NAME
// ============================================================

if (riderGreeting) {

    const name = user?.name || "Rider";

    const hour = new Date().getHours();

    let greeting = "Good evening";

    if (hour < 12) {
        greeting = "Good morning";
    } else if (hour < 18) {
        greeting = "Good afternoon";
    }

    riderGreeting.textContent =
        `${greeting}, ${name}.`;
}

// ============================================================
// LOGOUT
// ============================================================

const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {

    logoutBtn.addEventListener("click", () => {

        NovaAPI.logout(APP);

        window.location.href = "../login/index.html";
    });
}

// ============================================================
// INITIAL UI STATE
// ============================================================

function setSafetyStatus(
    status = "offline",
    message = ""
) {

    if (!safetyStatus) {
        return;
    }

    const normalized =
        String(status).toLowerCase();

    safetyStatus.textContent =
        normalized.toUpperCase();

    // --------------------------------------------------------
    // Icon
    // --------------------------------------------------------

    if (safetyIcon) {

        if (normalized === "safe") {

            safetyIcon.textContent =
                "verified_user";

        } else if (
            normalized === "warning"
        ) {

            safetyIcon.textContent =
                "warning";

        } else if (
            normalized === "danger"
        ) {

            safetyIcon.textContent =
                "emergency";

        } else {

            safetyIcon.textContent =
                "cloud_off";
        }
    }

    // --------------------------------------------------------
    // Status styling
    // --------------------------------------------------------

    safetyStatus.classList.remove(
        "text-primary",
        "text-warning",
        "text-danger",
        "text-on-surface-variant"
    );

    if (normalized === "safe") {

        safetyStatus.classList.add(
            "text-primary"
        );

    } else if (
        normalized === "warning"
    ) {

        safetyStatus.classList.add(
            "text-warning"
        );

    } else if (
        normalized === "danger"
    ) {

        safetyStatus.classList.add(
            "text-danger"
        );

    } else {

        safetyStatus.classList.add(
            "text-on-surface-variant"
        );
    }
}

// Start offline until telemetry arrives.
setSafetyStatus("offline");

// ============================================================
// GPS STATUS
// ============================================================

function setGPSStatus(
    connected = false
) {

    if (gpsStatus) {

        gpsStatus.textContent =
            connected
                ? "GPS ACTIVE"
                : "GPS OFFLINE";
    }

    if (gpsIndicator) {

        gpsIndicator.classList.remove(
            "bg-success",
            "bg-warning",
            "bg-danger"
        );

        if (connected) {

            gpsIndicator.classList.add(
                "bg-success"
            );

        } else {

            gpsIndicator.classList.add(
                "bg-danger"
            );
        }
    }
}

// ============================================================
// SPEED
// ============================================================

function updateSpeed(speed) {

    if (
        typeof speed !== "number" ||
        Number.isNaN(speed)
    ) {
        return;
    }

    if (currentSpeed) {

        currentSpeed.textContent =
            speed.toFixed(1);
    }

    if (speedProgress) {

        const percentage =
            Math.min(
                Math.max(
                    (speed / 80) * 100,
                    0
                ),
                100
            );

        speedProgress.style.width =
            `${percentage}%`;
    }
}

// ============================================================
// LEAN ANGLE
// ============================================================

function updateLeanAngle(
    roll,
    pitch
) {

    if (
        typeof roll !== "number" ||
        typeof pitch !== "number"
    ) {
        return;
    }

    const rollAbs =
        Math.abs(roll);

    const pitchAbs =
        Math.abs(pitch);

    // Use the larger deviation.
    const angle =
        Math.max(
            rollAbs,
            pitchAbs
        );

    if (leanAngle) {

        leanAngle.textContent =
            `${angle.toFixed(1)}°`;
    }

    if (leanStatus) {

        if (angle >= 45) {

            leanStatus.innerHTML = `
                <span class="material-symbols-outlined text-sm">
                    emergency
                </span>
                Critical angle
            `;

        } else if (angle >= 30) {

            leanStatus.innerHTML = `
                <span class="material-symbols-outlined text-sm">
                    warning
                </span>
                High lean angle
            `;

        } else {

            leanStatus.innerHTML = `
                <span class="material-symbols-outlined text-sm">
                    check_circle
                </span>
                Stable
            `;
        }
    }
}

// ============================================================
// ACCELERATION
// ============================================================

function updateAcceleration(
    accelG
) {

    if (
        typeof accelG !== "number" ||
        Number.isNaN(accelG)
    ) {
        return;
    }

    if (accelerationValue) {

        accelerationValue.innerHTML = `
            ${accelG.toFixed(2)}
            <span class="text-headline-md text-on-surface-variant">
                g
            </span>
        `;
    }

    if (accelerationStatus) {

        if (accelG >= 1.7) {

            accelerationStatus.textContent =
                "Vertical impact detected";

        } else {

            accelerationStatus.textContent =
                "Normal ride dynamics";
        }
    }
}

// ============================================================
// TELEMETRY
// ============================================================

let socket = null;

if (
    profile &&
    profile.riderId
) {

    socket = io(
        NOVASHIELDS_CONFIG.SOCKET_URL
    );

    // --------------------------------------------------------
    // CONNECT
    // --------------------------------------------------------

    socket.on(
        "connect",
        () => {

            setGPSStatus(true);

            socket.emit(
                "subscribe:rider",
                profile.riderId
            );

            console.log(
                "NovaShields Rider Socket connected."
            );
        }
    );

    // --------------------------------------------------------
    // DISCONNECT
    // --------------------------------------------------------

    socket.on(
        "disconnect",
        () => {

            setGPSStatus(false);

            setSafetyStatus(
                "offline"
            );

            console.log(
                "NovaShields Rider Socket disconnected."
            );
        }
    );

    // --------------------------------------------------------
    // LIVE TELEMETRY
    // --------------------------------------------------------

    socket.on(
        "telemetry:live",
        (data) => {

            console.log(
                "LIVE TELEMETRY:",
                data
            );

            // ------------------------------------------------
            // SPEED
            // ------------------------------------------------

            const speed =
                Number(
                    data.speedKmh
                    ??
                    data.speed
                );

            if (
                Number.isFinite(speed)
            ) {

                updateSpeed(
                    speed
                );
            }

            // ------------------------------------------------
            // ACCELERATION
            // ------------------------------------------------

            const accel =
                Number(
                    data.accelG
                    ??
                    data.acceleration_g
                    ??
                    data.acceleration
                );

            if (
                Number.isFinite(accel)
            ) {

                updateAcceleration(
                    accel
                );
            }

            // ------------------------------------------------
            // ROLL / PITCH
            // ------------------------------------------------

            const roll =
                Number(
                    data.roll
                    ??
                    data.rollDeg
                    ??
                    0
                );

            const pitch =
                Number(
                    data.pitch
                    ??
                    data.pitchDeg
                    ??
                    0
                );

            if (
                Number.isFinite(roll) &&
                Number.isFinite(pitch)
            ) {

                updateLeanAngle(
                    roll,
                    pitch
                );
            }

            // ------------------------------------------------
            // GPS
            // ------------------------------------------------

            const lat =
                Number(
                    data.lat
                    ??
                    data.latitude
                );

            const lng =
                Number(
                    data.lng
                    ??
                    data.longitude
                );

            if (
                Number.isFinite(lat) &&
                Number.isFinite(lng)
            ) {

                setGPSStatus(
                    true
                );
            }

            // ------------------------------------------------
            // SAFETY STATUS
            // ------------------------------------------------

            const eventType =
                String(
                    data.eventType
                    ??
                    data.event_type
                    ??
                    ""
                ).toLowerCase();

            if (
                eventType === "crash"
            ) {

                setSafetyStatus(
                    "danger",
                    "Crash detected"
                );

            } else if (
                eventType === "overspeed"
            ) {

                setSafetyStatus(
                    "danger",
                    "Overspeed detected"
                );

            } else if (
                eventType === "pothole"
            ) {

                setSafetyStatus(
                    "warning",
                    "Vertical impact detected"
                );

            } else {

                setSafetyStatus(
                    "safe"
                );
            }
        }
    );

    // ========================================================
    // TRIP START
    // ========================================================

    socket.on(
        "trip:started",
        () => {

            console.log(
                "Trip started."
            );
        }
    );

    // ========================================================
    // TRIP UPDATE
    // ========================================================

    socket.on(
        "trip:update",
        (data) => {

            if (rideDistance) {

                const distance =
                    Number(
                        data.distanceKm
                        ?? 0
                    );

                rideDistance.textContent =
                    `${distance.toFixed(1)} km`;
            }

            console.log(
                "Trip update:",
                data
            );
        }
    );

    // ========================================================
    // TRIP END
    // ========================================================

    socket.on(
        "trip:ended",
        () => {

            console.log(
                "Trip ended."
            );
        }
    );

} else {

    setGPSStatus(
        false
    );

    setSafetyStatus(
        "offline"
    );

    console.warn(
        "No rider profile/device linked."
    );
}

// ============================================================
// EMERGENCY BUTTON
// ============================================================

if (emergencyButton) {

    emergencyButton.addEventListener(
        "click",
        () => {

            console.log(
                "Emergency Response button clicked."
            );

            /*
             * IMPORTANT:
             *
             * Do NOT automatically create a
             * database emergency alert here yet.
             *
             * Our backend emergency escalation flow
             * is being developed around:
             *
             * Crash detection
             *      ↓
             * 30 second rider response
             *      ↓
             * Parent + Ambulance
             *      ↓
             * 30 minute unresolved
             *      ↓
             * Police
             *
             * This button will later open the
             * rider confirmation / cancellation UI.
             */
        }
    );
}