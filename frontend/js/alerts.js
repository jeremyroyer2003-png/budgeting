/**
 * alerts.js — Alert list with severity indicators and dismiss actions.
 */

async function loadAlerts() {
  const showRead = document.getElementById("showReadAlerts").checked;
  try {
    const alerts = await api.getAlerts({ show_read: showRead });
    renderAlerts(alerts);
  } catch (err) {
    document.getElementById("alertList").innerHTML =
      `<div class="empty-state">Error loading alerts.</div>`;
    showToast(err.message, "error");
  }
}

function renderAlerts(alerts) {
  const container = document.getElementById("alertList");
  if (!alerts.length) {
    container.innerHTML = `<div class="empty-state">No active alerts. You're all clear!</div>`;
    return;
  }

  container.innerHTML = alerts.map(a => {
    const icon = severityIcon(a.severity);
    const readClass = a.is_read ? "is-read" : "";
    const ts = new Date(a.created_at).toLocaleDateString("en-CA", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
    return `
      <div class="alert-item ${a.severity} ${readClass}" id="alert-${a.id}">
        <div class="alert-icon">
          <i data-feather="${icon}"></i>
        </div>
        <div class="alert-body">
          <div class="alert-message">${escAlert(a.message)}</div>
          <div class="alert-meta">
            ${a.category_name ? `<strong>${escAlert(a.category_name)}</strong> · ` : ""}
            ${ts}
            ${a.is_read ? " · Dismissed" : ""}
          </div>
        </div>
        ${!a.is_read ? `
          <button class="alert-dismiss" title="Dismiss" onclick="dismissAlert(${a.id})">
            <i data-feather="x"></i>
          </button>
        ` : ""}
      </div>
    `;
  }).join("");
  feather.replace();
}

function severityIcon(severity) {
  return { critical: "alert-octagon", warning: "alert-triangle", info: "info" }[severity] || "bell";
}

async function dismissAlert(alertId) {
  try {
    await api.markAlertRead(alertId);
    refreshAlertBadge();
    loadAlerts();
  } catch (err) {
    showToast(err.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("showReadAlerts").addEventListener("change", loadAlerts);

  document.getElementById("markAllReadBtn").addEventListener("click", async () => {
    try {
      await api.markAllRead();
      showToast("All alerts dismissed.", "success");
      refreshAlertBadge();
      loadAlerts();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
});

function escAlert(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
