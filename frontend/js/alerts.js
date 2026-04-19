/**
 * alerts.js — Alert list + weekly digest.
 */

async function loadAlerts() {
  const showRead = document.getElementById("showReadAlerts").checked;
  try {
    const [alerts] = await Promise.all([
      api.getAlerts({ show_read: showRead }),
      loadWeeklyDigest(),
    ]);
    renderAlerts(alerts);
  } catch (err) {
    document.getElementById("alertList").innerHTML =
      `<div class="empty-state">Error loading alerts.</div>`;
    showToast(err.message, "error");
  }
}

// ---- Weekly Digest ----

async function loadWeeklyDigest() {
  try {
    const data = await api.getWeeklySummary();
    renderWeeklyDigest(data);
  } catch (_) {
    document.getElementById("weeklyDigestBody").innerHTML =
      `<div class="empty-state small">Could not load weekly digest.</div>`;
  }
}

function renderWeeklyDigest(d) {
  const periodEl = document.getElementById("weeklyPeriod");
  const body     = document.getElementById("weeklyDigestBody");

  if (!d || !d.week_label) {
    periodEl.textContent = "";
    body.innerHTML = `<div class="empty-state small">No data yet — add some transactions to see your weekly digest.</div>`;
    return;
  }

  periodEl.textContent = d.week_label;

  const wowHtml = (() => {
    if (d.wow_pct === null || d.wow_pct === undefined) return "";
    const up   = d.wow_pct > 0;
    const flat = Math.abs(d.wow_pct) <= 2;
    const color = flat ? "var(--text-secondary)" : up ? "var(--danger)" : "var(--success)";
    const arrow = flat ? "→" : up ? "↑" : "↓";
    return `<span class="wow-badge" style="color:${color}">${arrow} ${Math.abs(d.wow_pct)}% vs prior week</span>`;
  })();

  const netColor = d.net >= 0 ? "var(--success)" : "var(--danger)";

  const catsHtml = d.top_categories.length
    ? d.top_categories.map(c => {
        const pct = d.total_expense > 0 ? Math.round(c.total / d.total_expense * 100) : 0;
        return `
          <div class="digest-cat-row">
            <span class="digest-cat-dot" style="background:${c.color}"></span>
            <span class="digest-cat-name">${escAlert(c.name)}</span>
            <div class="digest-cat-bar-wrap">
              <div class="digest-cat-bar-fill" style="width:${pct}%;background:${c.color}"></div>
            </div>
            <span class="digest-cat-amount">${fmtCurrency(c.total)}</span>
          </div>`;
      }).join("")
    : `<div class="empty-state small">No spending this week.</div>`;

  const dailyMax = Math.max(...d.daily.map(x => x.amount), 1);
  const dailyHtml = d.daily.map(day => {
    const h = Math.round((day.amount / dailyMax) * 48);
    return `
      <div class="digest-day-col">
        <div class="digest-day-bar-wrap">
          <div class="digest-day-bar" style="height:${h}px" title="${day.label}: ${fmtCurrency(day.amount)}"></div>
        </div>
        <div class="digest-day-label">${day.label}</div>
      </div>`;
  }).join("");

  const challengeHtml = d.challenge
    ? `<div class="digest-challenge">
        <div class="digest-challenge-label"><i data-feather="target"></i> This Week's Challenge</div>
        <div class="digest-challenge-text">${escAlert(d.challenge)}</div>
       </div>`
    : "";

  body.innerHTML = `
    <div class="digest-stats-row">
      <div class="digest-stat">
        <div class="digest-stat-label">Spent</div>
        <div class="digest-stat-value expense">${fmtCurrency(d.total_expense)}</div>
        ${wowHtml}
      </div>
      <div class="digest-stat">
        <div class="digest-stat-label">Income</div>
        <div class="digest-stat-value income">${fmtCurrency(d.total_income)}</div>
      </div>
      <div class="digest-stat">
        <div class="digest-stat-label">Net</div>
        <div class="digest-stat-value" style="color:${netColor}">${fmtCurrency(d.net)}</div>
      </div>
      <div class="digest-stat">
        <div class="digest-stat-label">Transactions</div>
        <div class="digest-stat-value">${d.tx_count}</div>
      </div>
    </div>

    <div class="digest-two-col">
      <div>
        <div class="digest-section-title">Top Categories</div>
        <div class="digest-cats">${catsHtml}</div>
      </div>
      <div>
        <div class="digest-section-title">Daily Spending</div>
        <div class="digest-daily">${dailyHtml}</div>
      </div>
    </div>

    ${challengeHtml}
  `;
  if (window.feather) feather.replace();
}

// ---- Alert list ----

function renderAlerts(alerts) {
  const container = document.getElementById("alertList");
  // Filter out weekly_summary from the regular list — they show in the digest card
  const regular = alerts.filter(a => a.type !== "weekly_summary");
  if (!regular.length) {
    container.innerHTML = `<div class="empty-state">No active alerts. You're all clear!</div>`;
    return;
  }

  container.innerHTML = regular.map(a => {
    const icon = severityIcon(a.severity);
    const readClass = a.is_read ? "is-read" : "";
    const ts = new Date(a.created_at).toLocaleDateString("en-CA", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
    return `
      <div class="alert-item ${a.severity} ${readClass}" id="alert-${a.id}">
        <div class="alert-icon"><i data-feather="${icon}"></i></div>
        <div class="alert-body">
          <div class="alert-message">${escAlert(a.message)}</div>
          <div class="alert-meta">
            ${a.category_name ? `<strong>${escAlert(a.category_name)}</strong> · ` : ""}
            ${ts}${a.is_read ? " · Dismissed" : ""}
          </div>
        </div>
        ${!a.is_read ? `
          <button class="alert-dismiss" title="Dismiss" onclick="dismissAlert(${a.id})">
            <i data-feather="x"></i>
          </button>` : ""}
      </div>`;
  }).join("");
  if (window.feather) feather.replace();
}

function severityIcon(s) {
  return { critical: "alert-octagon", warning: "alert-triangle", info: "info" }[s] || "bell";
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

  document.getElementById("refreshWeeklyBtn").addEventListener("click", async () => {
    document.getElementById("weeklyDigestBody").innerHTML =
      `<div class="empty-state small">Refreshing…</div>`;
    await loadWeeklyDigest();
  });
});

function escAlert(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
