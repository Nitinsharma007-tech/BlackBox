const APP = "guardian";
const REFRESH_MS = 5000;

// ============================================================
// AUTH
// ============================================================

const token = NovaAPI.getToken(APP);

if (!token) {
    window.location.href = "../login/index.html";
}

const user = NovaAPI.getUser(APP);

let currentDashboardData = null;


// ============================================================
// GET PARENT ID
// ============================================================

function getParentId() {
    return (
        user?.profile_id ||
        user?.parent_id ||
        "PT001"
    );
}


// ============================================================
// HELPERS
// ============================================================

function formatDateTime(value) {

    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "—";
    }

    return date.toLocaleString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}


function getFirstRider(data) {

    if (
        Array.isArray(data?.riders) &&
        data.riders.length > 0
    ) {
        return data.riders[0];
    }

    return null;
}


function getTelemetry(riderItem) {
    return riderItem?.latest_telemetry || {};
}


function updateText(element, value) {

    if (element) {
        element.textContent = value;
    }
}


// ============================================================
// UPDATE ORIGINAL UI
// ============================================================

function updateOriginalUI(data) {

    const riderItem = getFirstRider(data);

    const rider =
        riderItem?.rider || {};

    const vehicle =
        riderItem?.vehicle || {};

    const telemetry =
        getTelemetry(riderItem);

    const safety =
        riderItem?.safety_status || {};


    // ========================================================
    // RIDER NAME
    // ========================================================

    const riderName =
        document.getElementById("riderName");

    if (riderName) {

        riderName.textContent =
            rider.full_name ||
            rider.rider_id ||
            "Rider";

    }


    // ========================================================
    // VEHICLE
    // ========================================================

    const vehicleName =
        document.getElementById("vehicleName");

    if (vehicleName) {

        vehicleName.textContent =
            [
                vehicle.registration_number,
                vehicle.make,
                vehicle.model
            ]
                .filter(Boolean)
                .join(" • ") ||
            "Vehicle";

    }


    // ========================================================
    // TELEMETRY CARDS
    // ========================================================

    const telemetryCards =
        document.querySelectorAll(
            ".bg-surface-container-lowest\\/50.rounded-xl.p-4.border"
        );


    // ========================================================
    // SPEED
    // ========================================================

    const speed =
        Number(telemetry.speed);

    const speedCard =
        telemetryCards[0];

    if (speedCard) {

        const speedValue =
            speedCard.querySelector(
                ".text-4xl.font-display-lg.text-on-surface.font-extrabold"
            );

        if (speedValue) {

            speedValue.textContent =
                Number.isFinite(speed)
                    ? speed.toFixed(1)
                    : "—";

        }


        // Speed progress bar
        const speedBar =
            speedCard.querySelector(
                ".h-full.bg-primary-container"
            );

        if (speedBar) {

            const percentage =
                Number.isFinite(speed)
                    ? Math.min(
                        100,
                        Math.max(0, speed)
                    )
                    : 0;

            speedBar.style.width =
                `${percentage}%`;

        }

    }


    // ========================================================
    // LEAN ANGLE
    // ========================================================

    const roll =
        Number(telemetry.roll);

    const pitch =
        Number(telemetry.pitch);

    let lean = null;


    if (
        Number.isFinite(roll) &&
        Number.isFinite(pitch)
    ) {

        lean =
            Math.abs(roll) >= Math.abs(pitch)
                ? roll
                : pitch;

    }

    else if (
        Number.isFinite(roll)
    ) {

        lean = roll;

    }

    else if (
        Number.isFinite(pitch)
    ) {

        lean = pitch;

    }


    const leanCard =
        telemetryCards[1];

    if (leanCard) {

        const leanValue =
            leanCard.querySelector(
                ".text-4xl.font-display-lg.text-on-surface.font-extrabold"
            );

        if (leanValue) {

            leanValue.textContent =
                lean === null
                    ? "—"
                    : `${Math.abs(lean).toFixed(1)}°`;

        }


        const leanDirection =
            leanCard.querySelector(
                ".text-sm.font-bold.text-on-surface-variant"
            );

        if (leanDirection) {

            if (lean === null) {

                leanDirection.textContent = "—";

            }

            else {

                leanDirection.textContent =
                    lean < 0
                        ? "L"
                        : "R";

            }

        }


        // Lean bar
        const leanBar =
            leanCard.querySelector(
                ".absolute.top-0.left-1\\/2.h-full.bg-primary-container"
            );

        if (leanBar) {

            if (lean === null) {

                leanBar.style.width = "0%";

            }

            else {

                const percentage =
                    Math.min(
                        50,
                        Math.abs(lean) / 90 * 50
                    );

                leanBar.style.width =
                    `${percentage}%`;

                leanBar.style.left = "50%";

                if (lean < 0) {

                    leanBar.style.transform =
                        "translateX(-100%)";

                    leanBar.classList.remove(
                        "rounded-r-full"
                    );

                    leanBar.classList.add(
                        "rounded-l-full"
                    );

                }

                else {

                    leanBar.style.transform = "";

                    leanBar.classList.remove(
                        "rounded-l-full"
                    );

                    leanBar.classList.add(
                        "rounded-r-full"
                    );

                }

            }

        }

    }


    // ========================================================
    // MAP LOCATION
    // ========================================================

    const locationLabels =
        document.querySelectorAll(
            ".glass-active .font-bold.text-on-surface.text-sm"
        );


    locationLabels.forEach(
        element => {

            if (
                telemetry.latitude !== undefined &&
                telemetry.longitude !== undefined &&
                telemetry.latitude !== null &&
                telemetry.longitude !== null
            ) {

                const lat =
                    Number(telemetry.latitude);

                const lon =
                    Number(telemetry.longitude);

                if (
                    Number.isFinite(lat) &&
                    Number.isFinite(lon)
                ) {

                    element.textContent =
                        `${lat.toFixed(5)}, ${lon.toFixed(5)}`;

                }

                else {

                    element.textContent =
                        "Location unavailable";

                }

            }

            else {

                element.textContent =
                    "Location unavailable";

            }

        }
    );


    // ========================================================
    // MAP RIDER LABEL
    // ========================================================

    const mapRiderText =
        document.querySelector(
            ".absolute.top-1\\/2.left-1\\/2 .bg-primary-container"
        );

    if (mapRiderText) {

        mapRiderText.textContent =
            `${rider.full_name || rider.rider_id || "Rider"} • ` +
            `${Number.isFinite(speed) ? speed.toFixed(1) : "—"} km/h`;

    }


    // ========================================================
    // SYSTEM STATUS
    // ========================================================

    const statusPill =
        document.querySelector(
            ".inline-flex.items-center.gap-1\\.5.px-3"
        );


    const safetyStatus =
        String(
            safety.status || ""
        ).toLowerCase();


    const isOnline =
        Number(data?.summary?.online_riders || 0) > 0 ||
        [
            "safe",
            "at_risk",
            "danger"
        ].includes(safetyStatus);


    if (statusPill) {

        const dot =
            statusPill.querySelector(
                ".w-2.h-2.rounded-full"
            );

        if (dot) {

            dot.className =
                isOnline
                    ? "w-2 h-2 rounded-full bg-success animate-pulse"
                    : "w-2 h-2 rounded-full bg-danger";

        }


        const textNodes =
            [...statusPill.childNodes]
                .filter(
                    node =>
                        node.nodeType === Node.TEXT_NODE
                );


        if (textNodes.length) {

            textNodes[
                textNodes.length - 1
            ].textContent =
                isOnline
                    ? " System Active"
                    : " System Offline";

        }

    }


    // ========================================================
    // SUBTITLE
    // ========================================================

    const subtitle =
        document.getElementById(
            "riderSubtitle"
        );

    if (subtitle) {

        subtitle.textContent =
            `${data?.summary?.online_riders ?? 0} online • ` +
            `${data?.summary?.pending_alerts ?? 0} pending alerts`;

    }


    // ========================================================
    // ACTIVITY LOG
    // ========================================================

    updateActivityLog(data);

}


// ============================================================
// ACTIVITY LOG
// ============================================================

function updateActivityLog(data) {

    const activities =
        Array.isArray(data?.activities)
            ? data.activities.slice(0, 3)
            : [];


    const activityItems =
        document.querySelectorAll(
            ".glass-panel.rounded-2xl.p-card-padding.flex-1.flex.flex-col.min-h-\\[300px\\] .relative.pl-6"
        );


    // ========================================================
    // IMPORTANT:
    // HIDE ALL OLD/HARDCODED ACTIVITY ITEMS FIRST
    // ========================================================

    activityItems.forEach(item => {

        item.style.display = "none";

    });


    // ========================================================
    // REMOVE PREVIOUS EMPTY MESSAGE
    // ========================================================

    const oldEmptyMessage =
        document.querySelector(
            ".guardian-empty-activity"
        );

    if (oldEmptyMessage) {
        oldEmptyMessage.remove();
    }


    // ========================================================
    // NO ACTIVITIES
    // ========================================================

    if (activities.length === 0) {

        const activityContainer =
            document.querySelector(
                ".glass-panel.rounded-2xl.p-card-padding.flex-1.flex.flex-col.min-h-\\[300px\\]"
            );

        if (activityContainer) {

            const empty =
                document.createElement("div");

            empty.className =
                "guardian-empty-activity text-sm text-on-surface-variant";

            empty.style.padding =
                "24px 0";

            empty.textContent =
                "No recent safety activity.";

            activityContainer.appendChild(empty);

        }

        return;
    }


    // ========================================================
    // DISPLAY REAL API ACTIVITIES
    // ========================================================

    activities.forEach(
        (activity, index) => {

            const item =
                activityItems[index];

            if (!item) {
                return;
            }


            // Show this activity item
            item.style.display = "";


            // =================================================
            // TITLE
            // =================================================

            const title =
                item.querySelector(
                    ".font-bold.text-on-surface.text-sm, " +
                    ".font-bold.text-danger.text-sm"
                );


            const severity =
                String(
                    activity?.severity ||
                    "info"
                ).toLowerCase();


            if (title) {

                title.textContent =
                    activity?.title ||
                    activity?.event_type ||
                    "Safety Activity";


                if (
                    [
                        "critical",
                        "high",
                        "danger"
                    ].includes(severity)
                ) {

                    title.className =
                        "font-bold text-danger text-sm glow-text-danger";

                }

                else {

                    title.className =
                        "font-bold text-on-surface text-sm";

                }

            }


            // =================================================
            // TIME
            // =================================================

            const time =
                item.querySelector(
                    ".text-xs.text-outline.font-medium, " +
                    ".text-xs.text-danger\\/80.font-medium"
                );


            if (time) {

                time.textContent =
                    formatDateTime(
                        activity?.timestamp
                    );

            }


            // =================================================
            // MESSAGE
            // =================================================

            const message =
                item.querySelector(
                    ".text-sm.text-on-surface-variant"
                );


            if (message) {

                message.textContent =
                    activity?.message || "";

            }


            // =================================================
            // STATUS DOT
            // =================================================

            const dot =
                item.querySelector(
                    ".absolute.-left-\\[9px\\].top-1"
                );


            if (dot) {

                if (
                    [
                        "critical",
                        "high",
                        "danger"
                    ].includes(severity)
                ) {

                    dot.className =
                        "absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-danger border-2 border-white shadow-sm animate-pulse";

                }

                else if (
                    [
                        "medium",
                        "warning",
                        "at_risk"
                    ].includes(severity)
                ) {

                    dot.className =
                        "absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-warning border-2 border-white shadow-sm";

                }

                else {

                    dot.className =
                        "absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-primary-container border-2 border-white shadow-sm";

                }

            }

        }
    );

}


// ============================================================
// LOAD DASHBOARD
// ============================================================

async function loadDashboard() {

    try {

        const parentId =
            getParentId();


        console.log(
            "Loading Guardian dashboard for:",
            parentId
        );


        const data =
            await NovaAPI.getParentDashboardOverview(
                parentId
            );


        currentDashboardData =
            data;


        console.log(
            "NovaShields Guardian API:",
            data
        );


        updateOriginalUI(
            data
        );


    }

    catch (error) {

        console.error(
            "Guardian Dashboard API Error:",
            error
        );


        const subtitle =
            document.getElementById(
                "riderSubtitle"
            );


        if (subtitle) {

            subtitle.textContent =
                "Unable to load live telemetry";

        }

    }

}


// ============================================================
// START
// ============================================================

loadDashboard();


// ============================================================
// AUTO REFRESH
// ============================================================

setInterval(
    loadDashboard,
    REFRESH_MS
);