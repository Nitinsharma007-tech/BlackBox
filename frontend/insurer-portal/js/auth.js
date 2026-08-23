const APP = "insurer";

// Already logged in? skip straight to home.
if (NovaAPI.getToken(APP)) {
  window.location.href = "home.html";
}

const form = document.getElementById("loginForm");
const errorBox = document.getElementById("errorBox");
const submitBtn = document.getElementById("submitBtn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorBox.classList.remove("show");
  submitBtn.disabled = true;
  submitBtn.textContent = "Logging in...";

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  try {
    const user = await NovaAPI.login(APP, email, password);
    if (user.role !== "insurer") {
      throw new Error("This login is for insurers. Use the Rider or Guardian portal instead.");
    }
    window.location.href = "home.html";
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.add("show");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Log in";
  }
});
