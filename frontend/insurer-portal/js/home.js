const APP = "insurer";

const token = NovaAPI.getToken(APP);
if (!token) {
  window.location.href = "index.html";
}

const user = NovaAPI.getUser(APP);
document.getElementById("userName").textContent = user ? user.name : "Insurer";

document.getElementById("logoutBtn").addEventListener("click", () => {
  NovaAPI.logout(APP);
  window.location.href = "index.html";
});
