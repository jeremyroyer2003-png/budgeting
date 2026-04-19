/**
 * insights.js — Peer spending comparison and financial insights.
 */

async function loadInsights() {
  try {
    const data = await api.getPeerComparison();
    renderPeerComparison(data);
  } catch (err) {
    document.getElementById("insightsList").innerHTML =
      `<div class="empty-state">Error loading insights.</div>`;
    showToast(err.message, "error");
  }
}

function renderPeerComparison(data) {
  const container = document.getElementById("insightsList");

  if (!data || !data.categories || !data.categories.length) {
    container.innerHTML = `
      <div class="empty-state">
        Not enough data yet. Add a few months of transactions to see how your
        spending compares to a typical household.
      </div>`;
    return;
  }

  const periodEl = document.getElementById("insightsPeriod");
  if (periodEl) periodEl.textContent = `${data.period} · ${data.months}-month average`;

  const monthlyEl = document.getElementById("insightsMonthly");
  if (monthlyEl) monthlyEl.textContent = fmtCurrency(data.user_total_monthly) + "/mo";

  container.innerHTML = data.categories.map(c => {
    const maxPct = Math.max(c.user_pct, c.benchmark_pct, 1);
    const userW  = Math.round(c.user_pct  / maxPct * 100);
    const benchW = Math.round(c.benchmark_pct / maxPct * 100);

    const statusColor = c.status === "over"   ? "var(--danger)"
                      : c.status === "under"  ? "var(--success)"
                      :                          "var(--text-secondary)";
    const statusText  = c.status === "over"   ? `↑ ${(c.user_pct - c.benchmark_pct).toFixed(1)}% above avg`
                      : c.status === "under"  ? `↓ ${(c.benchmark_pct - c.user_pct).toFixed(1)}% below avg`
                      :                          "On par";

    return `
      <div class="peer-row">
        <div class="peer-label">
          <span class="peer-cat-name">${escIns(c.name)}</span>
          <span class="peer-status" style="color:${statusColor}">${statusText}</span>
        </div>
        <div class="peer-bars">
          <div class="peer-bar-row">
            <span class="peer-bar-label you">You</span>
            <div class="peer-bar-wrap">
              <div class="peer-bar-fill you" style="width:${userW}%"></div>
            </div>
            <span class="peer-bar-amt">${c.user_pct.toFixed(1)}% · ${fmtCurrency(c.user_monthly)}/mo</span>
          </div>
          <div class="peer-bar-row">
            <span class="peer-bar-label avg">Avg</span>
            <div class="peer-bar-wrap">
              <div class="peer-bar-fill avg" style="width:${benchW}%"></div>
            </div>
            <span class="peer-bar-amt">${c.benchmark_pct.toFixed(1)}% · ${fmtCurrency(c.benchmark_monthly)}/mo</span>
          </div>
        </div>
      </div>`;
  }).join("");
}

function escIns(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
