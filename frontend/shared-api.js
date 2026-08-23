// Shared by rider-app, guardian-dashboard, insurer-portal.
// Requires shared-config.js to be loaded first.
const NovaAPI = (function () {
  function tokenKey(app) {
    return `ns_token_${app}`;
  }
  function userKey(app) {
    return `ns_user_${app}`;
  }

  function profileKey(app) {
    return `ns_profile_${app}`;
  }

  function saveSession(app, token, user, profile) {
    localStorage.setItem(tokenKey(app), token);
    localStorage.setItem(userKey(app), JSON.stringify(user));
    if (profile) localStorage.setItem(profileKey(app), JSON.stringify(profile));
  }

  function getProfile(app) {
    const raw = localStorage.getItem(profileKey(app));
    return raw ? JSON.parse(raw) : null;
  }

  function getToken(app) {
    return localStorage.getItem(tokenKey(app));
  }

  function getUser(app) {
    const raw = localStorage.getItem(userKey(app));
    return raw ? JSON.parse(raw) : null;
  }

  function clearSession(app) {
  localStorage.removeItem(tokenKey(app));
  localStorage.removeItem(userKey(app));
  localStorage.removeItem(profileKey(app));
}

  async function request(path, { method = "GET", body, app } = {}) {
    const headers = { "Content-Type": "application/json" };
    const token = app ? getToken(app) : null;
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${NOVASHIELDS_CONFIG.API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || `Request failed (${res.status})`);
    }
    return data;
  }

  async function register(app, { name, email, phone, password, role }) {
    const data = await request("/auth/register", {
      method: "POST",
      body: { name, email, phone, password, role },
    });
    saveSession(app, data.token, data.user, data.profile);
    return data.user;
  }

  async function login(app, email, password) {
    const data = await request("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    saveSession(app, data.token, data.user, data.profile);
    return data.user;
  }

  function logout(app) {
    clearSession(app);
  }
    // ============================================================
  // PARENT DASHBOARD
  // ============================================================

  async function getParentDashboardOverview(parentId) {

    return await request(
        `/parent-dashboard/${encodeURIComponent(parentId)}/overview`,
        {
            method: "GET",
            app: "guardian",
        }
    );

}
  return { request, register, login, logout, getToken, getUser, getProfile, saveSession, getParentDashboardOverview };
})();
