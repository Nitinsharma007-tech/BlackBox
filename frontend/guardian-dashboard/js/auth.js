const APP = "guardian";

const form = document.getElementById("loginForm");
const errorBox = document.getElementById("errorBox");
const submitBtn = document.getElementById("submitBtn");

// ------------------------------------------------------------
// IMPORTANT:
// DO NOT AUTO-REDIRECT IF A TOKEN ALREADY EXISTS.
// Login page must always appear when index.html is opened.
// ------------------------------------------------------------

if (errorBox) {
    errorBox.classList.remove("show");
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    errorBox.classList.remove("show");

    submitBtn.disabled = true;
    submitBtn.textContent = "Signing in...";

    const email = document
        .getElementById("email")
        .value
        .trim();

    const password = document
        .getElementById("password")
        .value;

    try {

        const user = await NovaAPI.login(
            APP,
            email,
            password
        );

        // Make sure this is actually a Guardian account
        if (user.role !== "guardian") {
            throw new Error(
                "This login is for guardians. Use the Rider or Insurer portal instead."
            );
        }

        // Successful Guardian login
        window.location.href = "home.html";

    } catch (err) {

        console.error("Guardian login error:", err);

        errorBox.textContent =
            err.message || "Unable to log in. Please try again.";

        errorBox.classList.add("show");

    } finally {

        submitBtn.disabled = false;
        submitBtn.textContent = "Log in";

    }
});