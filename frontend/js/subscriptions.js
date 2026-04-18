/**
 * subscriptions.js — Detected recurring subscriptions page.
 */

async function loadSubscriptions() {
  try {
    const data = await api.getSubscriptions();
    renderSubscriptionSummary(data.summary);
    renderSubscriptionList(data.subscriptions);
  } catch (err) {
    document.getElementById("subList").innerHTML =
      `<div class="empty-state">Error loading subscriptions.</div>`;
    showToast(err.message, "error");
  }
}

function renderSubscriptionSummary(summary) {
  if (!summary || summary.count === 0) return;
  document.getElementById("subSummaryBar").style.display = "";
  document.getElementById("subCount").textContent   = summary.count;
  document.getElementById("subMonthly").textContent = fmtCurrency(summary.total_monthly);
  document.getElementById("subAnnual").textContent  = fmtCurrency(summary.total_annual);
}

function renderSubscriptionList(subs) {
  const container = document.getElementById("subList");
  if (!subs.length) {
    container.innerHTML = `
      <div class="empty-state">
        No recurring subscriptions detected yet.<br>
        Connect your bank accounts and add a few months of transactions to get started.
      </div>`;
    return;
  }

  container.innerHTML = `<div class="sub-grid">${subs.map(s => {
    const freqLabel = {
      weekly: "Weekly", biweekly: "Every 2 weeks",
      monthly: "Monthly", quarterly: "Quarterly", annual: "Annual",
    }[s.frequency] || s.frequency;

    const nextDate   = new Date(s.next_estimated + "T00:00:00");
    const daysUntil  = Math.round((nextDate - new Date()) / 86400000);
    const nextLabel  = daysUntil <= 0   ? "Due now"
                     : daysUntil === 1  ? "Tomorrow"
                     : daysUntil <= 7   ? `In ${daysUntil} days`
                     : fmtDate(s.next_estimated);

    const priceAlert = s.price_changed
      ? `<div class="sub-price-alert">
           <i data-feather="alert-triangle"></i>
           Price changed · Was ${s.price_history.slice(0, -1).map(p => fmtCurrency(p)).join(", ")}
         </div>`
      : "";

    const urgencyClass = daysUntil <= 3 ? "sub-card-urgent" : "";

    return `
      <div class="sub-card ${urgencyClass}">
        <div class="sub-card-header">
          <div class="sub-icon"><i data-feather="repeat"></i></div>
          <div class="sub-info">
            <div class="sub-name">${escSub(s.name)}</div>
            <div class="sub-freq">${freqLabel}${s.category_name ? ` · ${escSub(s.category_name)}` : ""}</div>
          </div>
          <div class="sub-amount">${fmtCurrency(s.last_amount)}</div>
        </div>
        ${priceAlert}
        <div class="sub-card-footer">
          <span class="sub-next ${daysUntil <= 3 ? "sub-next-soon" : ""}">
            <i data-feather="calendar"></i> Next: ${nextLabel}
          </span>
          <span class="sub-monthly">${fmtCurrency(s.monthly_cost)}/mo</span>
        </div>
      </div>
    `;
  }).join("")}</div>`;

  if (window.feather) feather.replace();
}

function escSub(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
