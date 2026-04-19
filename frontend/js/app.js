/**
 * app.js — Core SPA shell: routing, modal system, toasts, shared state.
 */

// ---- Dark mode (applied before render to prevent flash) ----
(function () {
  if (localStorage.getItem("clearbudget-theme") === "dark")
    document.documentElement.setAttribute("data-theme", "dark");
})();

// ---- Global state ----
const state = {
  currentPage: "dashboard",
  dashMonth:   new Date().getMonth() + 1,
  dashYear:    new Date().getFullYear(),
  budgetMonth: new Date().getMonth() + 1,
  budgetYear:  new Date().getFullYear(),
  categories:  [],
  accounts:    [],
};

// ---- Navigation ----
function navigateTo(page) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

  const pageEl = document.getElementById(`page-${page}`);
  if (pageEl) pageEl.classList.add("active");

  document.querySelectorAll(`.nav-item[data-page="${page}"]`).forEach(n => n.classList.add("active"));
  document.getElementById("topbarTitle").textContent = pageTitles[page] || page;
  state.currentPage = page;

  document.getElementById("sidebar").classList.remove("open");
  loadPage(page);
}

const pageTitles = {
  dashboard:     "Dashboard",
  transactions:  "Transactions",
  budgets:       "Budgets",
  goals:         "Financial Goals",
  subscriptions: "Subscriptions",
  insights:      "Insights",
  alerts:        "Alerts",
  family:        "Family Mode",
};

function loadPage(page) {
  switch (page) {
    case "dashboard":    loadDashboard();    break;
    case "transactions": loadTransactions(); break;
    case "budgets":      loadBudgets();      break;
    case "goals":        loadGoals();        break;
    case "subscriptions":loadSubscriptions();break;
    case "insights":     loadInsights();     break;
    case "alerts":       loadAlerts();       break;
    case "family":       loadFamily();       break;
  }
}

// ---- Dark mode toggle ----
function _applyTheme(theme) {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
  const btn = document.getElementById("darkToggle");
  if (btn) {
    btn.innerHTML = theme === "dark"
      ? '<i data-feather="sun"></i>'
      : '<i data-feather="moon"></i>';
    btn.title = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    if (window.feather) feather.replace();
  }
}

function toggleTheme() {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  localStorage.setItem("clearbudget-theme", next);
  _applyTheme(next);
}

// ---- Modal system ----
function openModal(id) {
  document.getElementById(id).classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

// ---- Toast ----
let _toastTimer = null;
function showToast(message, type = "") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

// ---- Confirm delete helper ----
function confirmDelete(message, onConfirm) {
  document.getElementById("confirmMessage").textContent = message;
  openModal("confirmModal");
  const btn = document.getElementById("confirmDeleteBtn");
  const handler = () => {
    closeModal("confirmModal");
    onConfirm();
    btn.removeEventListener("click", handler);
  };
  btn.removeEventListener("click", handler);
  btn.addEventListener("click", handler);
}

// ---- Shared formatters ----
function fmtCurrency(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-CA", { style: "currency", currency: "CAD", minimumFractionDigits: 2 }).format(n);
}

function fmtDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-CA", { month: "short", day: "numeric", year: "numeric" });
}

function monthLabel(month, year) {
  return new Date(year, month - 1, 1).toLocaleDateString("en-CA", { month: "long", year: "numeric" });
}

// ---- Populate dropdowns ----
async function loadSharedData() {
  try {
    [state.categories, state.accounts] = await Promise.all([api.getCategories(), api.getAccounts()]);
  } catch (e) {
    console.warn("Could not load shared data:", e);
  }
}

function populateCategorySelects(filterType = null) {
  const selects = document.querySelectorAll("#txCategory, #budgetCategory, #txCategoryFilter");
  selects.forEach(sel => {
    const prev = sel.value;
    if (sel.id === "txCategoryFilter") {
      sel.innerHTML = '<option value="">All categories</option>';
    } else {
      sel.innerHTML = '<option value="">— Select —</option>';
    }
    let cats = state.categories;
    if (filterType) cats = cats.filter(c => c.type === filterType);
    cats.forEach(c => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.name;
      sel.appendChild(opt);
    });
    if (prev) sel.value = prev;
  });
}

function populateAccountSelects() {
  const selects = document.querySelectorAll("#txAccount");
  selects.forEach(sel => {
    const prev = sel.value;
    sel.innerHTML = '<option value="">— Select —</option>';
    state.accounts.forEach(a => {
      const opt = document.createElement("option");
      opt.value = a.id;
      opt.textContent = a.name;
      sel.appendChild(opt);
    });
    if (prev) sel.value = prev;
  });
}

// ---- Wire up navigation ----
document.addEventListener("DOMContentLoaded", () => {
  // Apply saved theme
  _applyTheme(localStorage.getItem("clearbudget-theme") || "light");

  if (window.feather) feather.replace();

  // Nav links
  document.querySelectorAll(".nav-item, .card-link").forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      const page = link.dataset.page;
      if (page) navigateTo(page);
    });
  });

  // Hamburger
  document.getElementById("hamburger").addEventListener("click", () => {
    document.getElementById("sidebar").classList.toggle("open");
  });
  document.getElementById("sidebarClose").addEventListener("click", () => {
    document.getElementById("sidebar").classList.remove("open");
  });

  // Dark mode toggle
  document.getElementById("darkToggle").addEventListener("click", toggleTheme);

  // Modal close buttons
  document.querySelectorAll("[data-close]").forEach(btn => {
    btn.addEventListener("click", () => closeModal(btn.dataset.close));
  });

  // Close modal on overlay click
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", e => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });

  // Top bar "Add Transaction" button
  document.getElementById("topbarAddBtn").addEventListener("click", () => {
    openAddTxModal();
  });

  // Register PWA service worker
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }
});

// Called by auth.js once a valid session is confirmed
window._appBoot = async function _appBoot() {
  await loadSharedData();
  populateCategorySelects();
  populateAccountSelects();
  navigateTo("dashboard");
  refreshAlertBadge();
  api.generateWeeklySummary().catch(() => {});
};

async function refreshAlertBadge() {
  try {
    const alerts = await api.getAlerts();
    const badge = document.getElementById("alertBadge");
    badge.textContent = alerts.length > 0 ? alerts.length : "";
  } catch (_) {}
}

// re-export for use in page scripts
window.state = state;
window.openModal = openModal;
window.closeModal = closeModal;
window.showToast = showToast;
window.confirmDelete = confirmDelete;
window.fmtCurrency = fmtCurrency;
window.fmtDate = fmtDate;
window.monthLabel = monthLabel;
window.populateCategorySelects = populateCategorySelects;
window.populateAccountSelects = populateAccountSelects;
window.refreshAlertBadge = refreshAlertBadge;
window.loadSharedData = loadSharedData;
window.navigateTo = navigateTo;
