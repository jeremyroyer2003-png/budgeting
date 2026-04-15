/**
 * dashboard.js — Loads and renders the dashboard page.
 */

let trendChartInstance = null;
let categoryChartInstance = null;

async function loadDashboard() {
  const { dashMonth: month, dashYear: year } = state;

  // Update month label
  document.getElementById("currentMonthLabel").textContent = monthLabel(month, year);

  try {
    const data = await api.getDashboard({ month, year });
    renderSummaryCards(data);
    renderTrendChart(data.monthly_trend);
    renderCategoryChart(data.spending_by_category);
    renderDashBudgets(data.budget_summary);
    renderDashGoals(data.goals);
    renderDashAccounts(data.accounts);
    renderRecentTx(data.recent_transactions);

    // Update alert badge
    const badge = document.getElementById("alertBadge");
    badge.textContent = data.unread_alerts > 0 ? data.unread_alerts : "";
  } catch (err) {
    console.error("Dashboard load failed:", err);
    showToast("Could not load dashboard data. Is the backend running?", "error");
  }
}

function renderSummaryCards(data) {
  document.getElementById("statIncome").textContent      = fmtCurrency(data.total_income);
  document.getElementById("statExpenses").textContent    = fmtCurrency(data.total_expenses);

  const netEl = document.getElementById("statNet");
  netEl.textContent = fmtCurrency(data.net);
  netEl.style.color = data.net >= 0 ? "var(--success)" : "var(--danger)";

  document.getElementById("statSavingsRate").textContent = `${data.savings_rate}%`;
}

function renderTrendChart(trend) {
  const ctx = document.getElementById("trendChart").getContext("2d");
  if (trendChartInstance) trendChartInstance.destroy();

  trendChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: trend.map(t => t.label),
      datasets: [
        {
          label: "Income",
          data: trend.map(t => t.income),
          backgroundColor: "rgba(5, 150, 105, 0.75)",
          borderRadius: 4,
        },
        {
          label: "Expenses",
          data: trend.map(t => t.expenses),
          backgroundColor: "rgba(220, 38, 38, 0.75)",
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 12 } } },
        tooltip: {
          callbacks: {
            label: ctx => ` ${fmtCurrency(ctx.raw)}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: v => fmtCurrency(v),
            font: { size: 11 },
          },
          grid: { color: "rgba(0,0,0,.04)" },
        },
        x: { ticks: { font: { size: 11 } }, grid: { display: false } },
      },
    },
  });
}

function renderCategoryChart(categories) {
  const ctx = document.getElementById("categoryChart").getContext("2d");
  if (categoryChartInstance) categoryChartInstance.destroy();

  if (!categories.length) {
    document.getElementById("categoryLegend").innerHTML = '<div class="empty-state small">No expense data</div>';
    return;
  }

  categoryChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: categories.map(c => c.name),
      datasets: [{
        data: categories.map(c => c.total),
        backgroundColor: categories.map(c => c.color),
        borderWidth: 2,
        borderColor: "#fff",
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: ctx => ` ${ctx.label}: ${fmtCurrency(ctx.raw)}` },
        },
      },
    },
  });

  // Custom legend
  const legend = document.getElementById("categoryLegend");
  legend.innerHTML = categories.slice(0, 8).map(c => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${c.color}"></span>
      <span class="legend-name">${c.name}</span>
      <span class="legend-amount">${fmtCurrency(c.total)}</span>
    </div>
  `).join("");
}

function renderDashBudgets(summary) {
  const el = document.getElementById("dashBudgetList");
  if (!summary.length) {
    el.innerHTML = '<div class="empty-state small">No budgets set for this month.</div>';
    return;
  }
  el.innerHTML = summary.slice(0, 6).map(b => {
    const pct = Math.min(b.pct_used, 100);
    const fillClass = b.over_budget ? "over" : pct >= 80 ? "warn" : "good";
    return `
      <div class="budget-mini-item">
        <span class="budget-mini-name">
          <span class="cat-dot" style="background:${b.category_color};display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;"></span>
          ${b.category_name}
        </span>
        <div class="budget-mini-bar">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill ${fillClass}" style="width:${pct}%"></div>
          </div>
        </div>
        <span class="budget-mini-pct ${b.over_budget ? "amount-expense" : ""}">${b.pct_used}%</span>
      </div>
    `;
  }).join("");
}

function renderDashGoals(goals) {
  const el = document.getElementById("dashGoalList");
  if (!goals.length) {
    el.innerHTML = '<div class="empty-state small">No active goals.</div>';
    return;
  }
  el.innerHTML = goals.slice(0, 4).map(g => {
    const pct = g.progress_pct;
    const fillClass = pct >= 100 ? "good" : pct >= 50 ? "good" : "warn";
    return `
      <div class="goal-mini-item">
        <span class="goal-mini-name">${g.name}</span>
        <div class="goal-mini-bar">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill ${fillClass}" style="width:${pct}%"></div>
          </div>
        </div>
        <span class="goal-mini-pct">${pct}%</span>
      </div>
    `;
  }).join("");
}

function renderDashAccounts(accounts) {
  const el = document.getElementById("dashAccounts");
  if (!accounts.length) {
    el.innerHTML = '<div class="empty-state small">No accounts found.</div>';
    return;
  }
  const iconMap = { checking: "credit-card", savings: "piggy-bank", investment: "trending-up", credit: "credit-card", cash: "dollar-sign" };
  el.innerHTML = `<div class="accounts-row">` + accounts.map(a => `
    <div class="account-chip">
      <div class="account-chip-icon">
        <i data-feather="${iconMap[a.type] || "dollar-sign"}"></i>
      </div>
      <div>
        <div class="account-chip-label">${a.name}</div>
        <div class="account-chip-balance">${fmtCurrency(a.balance)}</div>
      </div>
    </div>
  `).join("") + `</div>`;
  feather.replace();
}

function renderRecentTx(txns) {
  const el = document.getElementById("dashRecentTx");
  if (!txns.length) {
    el.innerHTML = '<div class="empty-state small">No recent transactions.</div>';
    return;
  }
  el.innerHTML = txns.map(t => {
    const isIncome = t.type === "income";
    const bg = isIncome ? "var(--success-light)" : "var(--danger-light)";
    const color = isIncome ? "var(--success)" : "var(--danger)";
    const sign = isIncome ? "+" : "−";
    return `
      <div class="recent-tx-item">
        <div class="recent-tx-icon" style="background:${bg};color:${color}">
          ${(t.category_name || "?").charAt(0).toUpperCase()}
        </div>
        <div class="recent-tx-desc">
          <strong>${t.description || t.category_name || "Transaction"}</strong>
          <span>${fmtDate(t.date)} · ${t.account_name || ""}</span>
        </div>
        <div class="recent-tx-amount" style="color:${color}">
          ${sign}${fmtCurrency(t.amount)}
        </div>
      </div>
    `;
  }).join("");
}

// ---- Month navigation ----
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("prevMonth").addEventListener("click", () => {
    let { dashMonth: m, dashYear: y } = state;
    m--; if (m < 1) { m = 12; y--; }
    state.dashMonth = m; state.dashYear = y;
    loadDashboard();
  });

  document.getElementById("nextMonth").addEventListener("click", () => {
    let { dashMonth: m, dashYear: y } = state;
    m++; if (m > 12) { m = 1; y++; }
    state.dashMonth = m; state.dashYear = y;
    loadDashboard();
  });
});
