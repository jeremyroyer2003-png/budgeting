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
    renderInsightCards(data);
    renderHealthScore(data.health_score);
    renderProjection(data.projection);
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

function renderInsightCards(data) {
  // Daily insight banner
  const insightEl = document.getElementById("dailyInsightText");
  if (insightEl && data.daily_insight) {
    insightEl.textContent = data.daily_insight;
    document.getElementById("insightCard").style.display = "";
  }

  // Buffer days
  const bufferEl = document.getElementById("statBufferDays");
  if (bufferEl) {
    if (data.buffer_days != null) {
      bufferEl.textContent = data.buffer_days;
      const sub = document.getElementById("statBufferSub");
      if (sub) {
        const level = data.buffer_days >= 90 ? "excellent" : data.buffer_days >= 30 ? "good" : "low";
        sub.textContent = level === "excellent" ? "3+ months runway — excellent!" :
                          level === "good"      ? "30+ days — you're covered" :
                                                  "Less than 30 days — build your cushion";
        sub.className = `stat-sub buffer-${level}`;
      }
    } else {
      document.getElementById("bufferCard").style.display = "none";
    }
  }

  // Savings streak
  const streakEl = document.getElementById("statSavingsStreak");
  if (streakEl) {
    if (data.savings_streak != null && data.savings_streak > 0) {
      streakEl.textContent = data.savings_streak;
      const sub = document.getElementById("statStreakSub");
      if (sub) sub.textContent = data.savings_streak === 1 ? "month in a row — keep going!" :
                                  `consecutive months — ${data.savings_streak >= 3 ? "amazing streak!" : "great work!"}`;
    } else {
      document.getElementById("streakCard").style.display = "none";
    }
  }
}

function renderHealthScore(hs) {
  if (!hs) return;

  // Animate the SVG gauge arc
  const fill = document.getElementById("healthGaugeFill");
  if (fill) {
    const pct  = hs.score;        // 0-100
    const r    = 85;
    const cx   = 100, cy = 100;
    if (pct <= 0) {
      fill.setAttribute("d", `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx - r} ${cy}`);
    } else {
      const angle    = (pct / 100) * Math.PI;
      const ex       = cx - r * Math.cos(angle);
      const ey       = cy + r * Math.sin(angle);
      const largeArc = pct > 50 ? 1 : 0;
      fill.setAttribute("d", `M ${cx - r} ${cy} A ${r} ${r} 0 ${largeArc} 1 ${ex.toFixed(1)} ${ey.toFixed(1)}`);
    }
    fill.setAttribute("stroke", hs.color);
  }

  const numEl = document.getElementById("healthScoreNum");
  if (numEl) { numEl.textContent = hs.score; numEl.setAttribute("fill", hs.color); }
  const lblEl = document.getElementById("healthScoreLabel");
  if (lblEl) lblEl.textContent = hs.label;

  // Component bars
  const container = document.getElementById("healthComponents");
  const compMeta = {
    savings_rate:     { icon: "trending-up",  label: "Savings Rate" },
    budget_adherence: { icon: "sliders",       label: "Budget Adherence" },
    goal_progress:    { icon: "target",        label: "Goal Progress" },
    spending_trend:   { icon: "bar-chart-2",   label: "Spending Trend" },
  };
  container.innerHTML = Object.entries(hs.components).map(([key, comp]) => {
    const meta = compMeta[key] || { icon: "circle", label: key };
    const pct  = (comp.score / comp.max) * 100;
    const barColor = pct >= 80 ? "var(--success)" : pct >= 50 ? "var(--warning)" : "var(--danger)";
    return `
      <div class="health-comp-row">
        <div class="health-comp-label">
          <i data-feather="${meta.icon}"></i>${meta.label}
        </div>
        <div class="health-comp-bar-wrap">
          <div class="health-comp-bar-fill" style="width:${pct}%;background:${barColor}"></div>
        </div>
        <div class="health-comp-pts">${comp.score}<span>/25</span></div>
        <div class="health-comp-detail">${comp.detail}</div>
        ${comp.tip ? `<div class="health-comp-tip">${comp.tip}</div>` : ""}
      </div>
    `;
  }).join("");
  if (window.feather) feather.replace();
}

function renderProjection(p) {
  const card = document.getElementById("projectionCard");
  if (!p) { card.style.display = "none"; return; }
  card.style.display = "";

  // Progress bar — how far through the month we are
  document.getElementById("projMonthFill").style.width = `${p.month_pct}%`;
  document.getElementById("projMonthLabel").textContent =
    `Day ${p.days_elapsed} of ${p.days_in_month} · ${p.days_remaining} day${p.days_remaining !== 1 ? "s" : ""} remaining`;

  // Confidence badge
  const badge = document.getElementById("projConfidence");
  badge.textContent = { low: "Low confidence", medium: "Medium confidence", high: "High confidence" }[p.confidence] || "";
  badge.className = `proj-confidence-badge ${p.confidence}`;

  // Values
  document.getElementById("projIncome").textContent  = fmtCurrency(p.projected_income);
  document.getElementById("projExpense").textContent = fmtCurrency(p.projected_expense);

  const netEl = document.getElementById("projNet");
  netEl.textContent = fmtCurrency(p.projected_net);
  netEl.style.color = p.projected_net >= 0 ? "var(--success)" : "var(--danger)";

  // Subscriptions note
  const note = document.getElementById("projSubsNote");
  if (p.subs_due_count > 0) {
    note.style.display = "";
    note.innerHTML = `<i data-feather="repeat"></i> ${p.subs_due_count} subscription${p.subs_due_count > 1 ? "s" : ""} due before month-end · ${fmtCurrency(p.subs_due_total)} already included above`;
    if (window.feather) feather.replace();
  } else {
    note.style.display = "none";
  }
}

function renderTrendChart(trend) {
  const canvas = document.getElementById("trendChart");
  if (!window.Chart || !canvas) return;
  const ctx = canvas.getContext("2d");
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
  const canvas = document.getElementById("categoryChart");
  if (!window.Chart || !canvas) {
    document.getElementById("categoryLegend").innerHTML = '<div class="empty-state small">Charts unavailable</div>';
    return;
  }
  const ctx = canvas.getContext("2d");
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
  // "piggy-bank" is not in the Feather icon set — use "archive" for savings accounts
  const iconMap = { checking: "credit-card", savings: "archive", investment: "trending-up", credit: "credit-card", cash: "dollar-sign" };
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
  if (window.feather) feather.replace();
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
