// ============================================================
// NOVASHIELDS COMMON LOGIN
// Guardian + Rider + Insurer
// ============================================================

const ROLE_CONFIG = {
    guardian: {
        label: "Guardian",
        app: "guardian",
        home: "../guardian-dashboard/home.html",
        subtitle:
            "Monitor rider safety, live location and emergency alerts."
    },

    rider: {
        label: "Rider",
        app: "rider",
        home: "../rider-app/home.html",
        subtitle:
            "Access your rider dashboard and vehicle safety information."
    },

    insurer: {
        label: "Insurer",
        app: "insurer",
        home: "../insurer-portal/home.html",
        subtitle:
            "Access vehicle safety records, incidents and insurance data."
    }
};


// ============================================================
// DEFAULT ROLE
// ============================================================

let selectedRole = "guardian";


// ============================================================
// ELEMENTS
// ============================================================

const form = document.getElementById("loginForm");
const errorBox = document.getElementById("errorBox");
const submitBtn = document.getElementById("submitBtn");

const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");

const portalTitle = document.getElementById("portalTitle");
const portalSubtitle = document.getElementById("portalSubtitle");

const roleButtons = document.querySelectorAll(".role-btn");


// ============================================================
// ERROR HANDLING
// ============================================================

function showError(message) {

    if (!errorBox) return;

    errorBox.textContent =
        message || "Unable to log in. Please try again.";

    errorBox.classList.add("show");
}


function clearError() {

    if (!errorBox) return;

    errorBox.textContent = "";
    errorBox.classList.remove("show");
}


// ============================================================
// ROLE UI
// ============================================================

function updateRoleUI(role) {

    const config = ROLE_CONFIG[role];

    if (!config) return;

    selectedRole = role;

    roleButtons.forEach((button) => {

        const active =
            button.dataset.role === role;

        button.classList.toggle(
            "active",
            active
        );

        if (active) {

            button.classList.remove(
                "text-on-surface-variant"
            );

            button.classList.add(
                "text-primary"
            );

        } else {

            button.classList.remove(
                "text-primary"
            );

            button.classList.add(
                "text-on-surface-variant"
            );
        }
    });


    if (portalTitle) {

        portalTitle.textContent =
            `${config.label} Login`;
    }


    if (portalSubtitle) {

        portalSubtitle.textContent =
            config.subtitle;
    }


    clearError();
}


// ============================================================
// ROLE SELECTION
// ============================================================

roleButtons.forEach((button) => {

    button.addEventListener("click", () => {

        const role =
            button.dataset.role;

        if (!ROLE_CONFIG[role]) {
            return;
        }

        updateRoleUI(role);
    });

});


// ============================================================
// INITIAL LOGIN PAGE
// ============================================================

// IMPORTANT:
// NEVER AUTO-REDIRECT HERE.
//
// The common login page must ALWAYS appear
// when /login/index.html is opened.
//
// Existing tokens are intentionally ignored.
// ============================================================

updateRoleUI("guardian");


// ============================================================
// LOGIN
// ============================================================

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    clearError();

    submitBtn.disabled = true;
    submitBtn.textContent = "Signing in...";


    const email =
        emailInput.value.trim();

    const password =
        passwordInput.value;

    const config =
        ROLE_CONFIG[selectedRole];


    try {

        if (!config) {

            throw new Error(
                "Please select a login portal."
            );
        }


        if (!email || !password) {

            throw new Error(
                "Please enter your email and password."
            );
        }


        console.log(
            `NovaShields login: ${config.label}`
        );


        // ====================================================
        // CALL EXISTING SHARED API
        // ====================================================

        const user =
            await NovaAPI.login(
                config.app,
                email,
                password
            );


        // ====================================================
        // ROLE VALIDATION
        // ====================================================

        if (
            !user ||
            user.role !== config.app
        ) {

            // Remove wrongly saved session
            NovaAPI.logout(config.app);


            throw new Error(
                `This account is not a ${config.label} account. ` +
                `Please select the correct portal.`
            );
        }


        // ====================================================
        // SUCCESS
        // ====================================================

        console.log(
            `Login successful: ${config.label}`
        );


        window.location.href =
            config.home;


    } catch (err) {

        console.error(
            "NovaShields login error:",
            err
        );


        showError(
            err.message ||
            "Unable to log in. Please try again."
        );


    } finally {

        submitBtn.disabled = false;

        submitBtn.textContent =
            "Log in";
    }

});