/**
 * auth.js — Login, register, logout, and token management.
 *
 * Flow:
 *   1. On page load: check localStorage for JWT.
 *   2. If no token → show auth screen, hide app.
 *   3. User logs in / registers → receive token → store → show app.
 *   4. Logout → clear token → show auth screen.
 *
 * The token is read by api.js and sent as "Authorization: Bearer <token>"
 * on every API request. A 401 response auto-triggers logout.
 */

const TOKEN_KEY = "cb_token";
const USER_KEY  = "cb_user";

// ── Token helpers ─────────────────────────────────────────────────────────────

function getToken()              { return localStorage.getItem(TOKEN_KEY); }
function setToken(t)             { localStorage.setItem(TOKEN_KEY, t); }
function getStoredUser()         { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } }
function setStoredUser(u)        { localStorage.setItem(USER_KEY, JSON.stringify(u)); }
function clearAuth()             { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); }
function isAuthenticated()       { return !!getToken(); }

// ── Show / hide app vs auth screen ────────────────────────────────────────────

function showApp() {
  document.getElementById("authScreen").style.display  = "none";
  document.getElementById("sidebar").style.display     = "";
  document.querySelector(".main-wrapper").style.display = "";
}

function showAuthScreen(panel = "login") {
  document.getElementById("authScreen").style.display  = "flex";
  document.getElementById("sidebar").style.display     = "none";
  document.querySelector(".main-wrapper").style.display = "none";
  _switchPanel(panel);
}

function _switchPanel(which) {
  document.getElementById("loginPanel").style.display    = which === "login"    ? "" : "none";
  document.getElementById("registerPanel").style.display = which === "register" ? "" : "none";
  // Clear errors when switching
  _clearError("loginError");
  _clearError("registerError");
}

// ── Populate sidebar user info ────────────────────────────────────────────────

function updateSidebarUser(user) {
  if (!user) return;
  const initials = user.name
    .split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
  document.getElementById("userAvatar").textContent = initials;
  document.getElementById("userName").textContent   = user.name;
  document.getElementById("userEmail").textContent  = user.email;
}

// ── Auth actions ──────────────────────────────────────────────────────────────

async function login(email, password) {
  const data = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  _onAuthSuccess(data);
}

async function register(name, email, password) {
  const data = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
  _onAuthSuccess(data);
}

function logout() {
  clearAuth();
  showAuthScreen("login");
}

function _onAuthSuccess({ access_token, user }) {
  setToken(access_token);
  setStoredUser(user);
  updateSidebarUser(user);
  showApp();
  // Boot the app now that we have a valid token
  if (window._appBoot) window._appBoot();
}

// ── Error display helpers ──────────────────────────────────────────────────────

function _showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.style.display = "block";
}

function _clearError(id) {
  const el = document.getElementById(id);
  if (el) { el.textContent = ""; el.style.display = "none"; }
}

function _setLoading(btn, loading) {
  btn.disabled = loading;
  btn.textContent = loading ? "Please wait…" : btn.dataset.label;
}

// ── Wire up forms ─────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  // Store button labels for restore after loading state
  document.getElementById("loginBtn").dataset.label    = "Sign in";
  document.getElementById("registerBtn").dataset.label = "Create account";

  // Eye toggle — show/hide password
  document.querySelectorAll(".pw-eye").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.target);
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      btn.innerHTML = isHidden
        ? '<i data-feather="eye-off"></i>'
        : '<i data-feather="eye"></i>';
      if (window.feather) feather.replace();
    });
  });

  // Panel toggle links
  document.getElementById("showRegister").addEventListener("click", e => {
    e.preventDefault(); _switchPanel("register");
  });
  document.getElementById("showLogin").addEventListener("click", e => {
    e.preventDefault(); _switchPanel("login");
  });

  // Login form
  document.getElementById("loginForm").addEventListener("submit", async e => {
    e.preventDefault();
    _clearError("loginError");
    const btn = document.getElementById("loginBtn");
    _setLoading(btn, true);
    try {
      await login(
        document.getElementById("loginEmail").value.trim(),
        document.getElementById("loginPassword").value,
      );
    } catch (err) {
      _showError("loginError", err.message || "Login failed. Please try again.");
    } finally {
      _setLoading(btn, false);
    }
  });

  // Register form
  document.getElementById("registerForm").addEventListener("submit", async e => {
    e.preventDefault();
    _clearError("registerError");
    const pw      = document.getElementById("regPassword").value;
    const pwConfirm = document.getElementById("regPasswordConfirm").value;
    if (pw.length < 8) {
      _showError("registerError", "Password must be at least 8 characters.");
      return;
    }
    if (pw !== pwConfirm) {
      _showError("registerError", "Passwords do not match.");
      return;
    }
    const btn = document.getElementById("registerBtn");
    _setLoading(btn, true);
    try {
      await register(
        document.getElementById("regName").value.trim(),
        document.getElementById("regEmail").value.trim(),
        pw,
      );
    } catch (err) {
      _showError("registerError", err.message || "Registration failed. Please try again.");
    } finally {
      _setLoading(btn, false);
    }
  });

  // Logout button
  document.getElementById("logoutBtn").addEventListener("click", () => {
    logout();
  });

  // ── Boot sequence ──────────────────────────────────────────────────────────
  if (isAuthenticated()) {
    updateSidebarUser(getStoredUser());
    showApp();
    // app.js will call _appBoot via window._appBoot after DOMContentLoaded
  } else {
    showAuthScreen("login");
  }
});

// Expose for app.js to detect
window.isAuthenticated  = isAuthenticated;
window.getToken         = getToken;
window.logout           = logout;
window.updateSidebarUser = updateSidebarUser;
