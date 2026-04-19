/**
 * budgets.js — Budget cards with progress bars and add/edit.
 */

async function loadBudgets() {
  const { budgetMonth: month, budgetYear: year } = state;
  document.getElementById("budgetMonthLabel").textContent = monthLabel(month, year);

  try {
    const summary = await api.getBudgetSummary({ month, year });
    renderBudgetCards(summary, month, year);
  } catch (err) {
    document.getElementById("budgetCards").innerHTML =
      `<div class="empty-state">Error loading budgets.</div>`;
    showToast(err.message, "error");
  }
}

function renderBudgetCards(summary, month, year) {
  const container = document.getElementById("budgetCards");
  if (!summary.length) {
    container.innerHTML = `
      <div class="empty-state">
        No budgets set for ${monthLabel(month, year)}.<br>
        <br><button class="btn btn-primary" onclick="openBudgetModal()"><i data-feather="plus"></i> Set Budget</button>
      </div>`;
    if (window.feather) feather.replace();
    return;
  }

  // Compute days remaining in this month (for current month only)
  const today       = new Date();
  const isCurrentMonth = (month === today.getMonth() + 1 && year === today.getFullYear());
  const daysInMonth = new Date(year, month, 0).getDate();
  const daysElapsed = isCurrentMonth ? today.getDate() : daysInMonth;
  const daysLeft    = isCurrentMonth ? daysInMonth - today.getDate() : 0;

  container.innerHTML = summary.map(b => {
    const barWidth  = Math.min(b.pct_used, 100);
    const fillClass = b.over_budget ? "over" : b.pct_used >= 80 ? "warn" : "good";
    const pctLabel  = b.over_budget
      ? `<span class="pct-over">${b.pct_used.toFixed(0)}% used</span>`
      : `${b.pct_used.toFixed(0)}% used`;

    // Actionable bottom line
    let bottomLine = "";
    if (b.over_budget) {
      const over = Math.abs(b.remaining);
      bottomLine = `<div class="budget-action-line over">
        <i data-feather="alert-circle"></i>
        Over by <strong>${fmtCurrency(over)}</strong>${isCurrentMonth && daysLeft > 0
          ? ` — spend <strong>${fmtCurrency(over / daysLeft)}/day</strong> less to recover`
          : ""}
      </div>`;
    } else if (b.pct_used >= 80 && isCurrentMonth && daysLeft > 0) {
      const dailyBudget = b.remaining / daysLeft;
      bottomLine = `<div class="budget-action-line warn">
        <i data-feather="alert-triangle"></i>
        <strong>${fmtCurrency(b.remaining)} left</strong> for ${daysLeft} day${daysLeft !== 1 ? "s" : ""}
        — <strong>${fmtCurrency(dailyBudget)}/day</strong> to stay on track
      </div>`;
    } else if (!b.over_budget && b.remaining > 0) {
      if (isCurrentMonth && daysLeft > 0) {
        const dailyBudget = b.remaining / daysLeft;
        bottomLine = `<div class="budget-action-line good">
          <i data-feather="check-circle"></i>
          <strong>${fmtCurrency(b.remaining)} left</strong> · ${fmtCurrency(dailyBudget)}/day for ${daysLeft} more day${daysLeft !== 1 ? "s" : ""}
        </div>`;
      } else {
        bottomLine = `<div class="budget-action-line good">
          <i data-feather="check-circle"></i>
          Finished ${fmtCurrency(b.remaining)} under budget — great discipline!
        </div>`;
      }
    }

    return `
      <div class="budget-card">
        <div class="budget-card-header">
          <div class="budget-cat">
            <span class="cat-dot" style="background:${b.category_color}"></span>
            ${escBudget(b.category_name)}
          </div>
          <div class="budget-amounts">
            <span class="actual ${b.over_budget ? "over" : ""}">${fmtCurrency(b.actual_amount)}</span>
            <span> / ${fmtCurrency(b.target_amount)}</span>
          </div>
        </div>
        <div class="progress-wrap">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill ${fillClass}" style="width:${barWidth}%"></div>
          </div>
        </div>
        <div class="budget-footer">
          <span>${pctLabel}</span>
        </div>
        ${bottomLine}
        <div style="display:flex;justify-content:flex-end;margin-top:8px;">
          <button class="btn btn-ghost btn-sm" onclick="openBudgetModal(${b.budget_id},${b.category_id},${b.target_amount})">
            Edit
          </button>
          <button class="btn btn-ghost btn-sm" onclick="deleteBudget(${b.budget_id})" style="color:var(--danger)">
            Delete
          </button>
        </div>
      </div>
    `;
  }).join("");
  if (window.feather) feather.replace();
}

function openBudgetModal(budgetId = null, catId = null, amount = null) {
  document.getElementById("budgetForm").reset();

  // Populate expense categories only
  const sel = document.getElementById("budgetCategory");
  sel.innerHTML = '<option value="">— Select category —</option>';
  state.categories.filter(c => c.type === "expense").forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.name;
    sel.appendChild(opt);
  });

  if (catId)   sel.value = catId;
  if (amount)  document.getElementById("budgetAmount").value = amount;

  const { budgetMonth: m, budgetYear: y } = state;
  document.getElementById("budgetMonth").value =
    `${y}-${String(m).padStart(2, "0")}`;

  openModal("budgetModal");
}

async function deleteBudget(budgetId) {
  confirmDelete("Delete this budget target?", async () => {
    try {
      await api.deleteBudget(budgetId);
      showToast("Budget deleted.", "success");
      loadBudgets();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("addBudgetBtn").addEventListener("click", () => openBudgetModal());

  document.getElementById("budgetForm").addEventListener("submit", async e => {
    e.preventDefault();
    const catId  = parseInt(document.getElementById("budgetCategory").value);
    const amount = parseFloat(document.getElementById("budgetAmount").value);
    const mon    = document.getElementById("budgetMonth").value; // "YYYY-MM"
    const [y, m] = mon.split("-");

    if (!catId) { showToast("Please select a category.", "error"); return; }

    try {
      await api.setBudget({ category_id: catId, target_amount: amount, month: parseInt(m), year: parseInt(y) });
      closeModal("budgetModal");
      showToast("Budget saved.", "success");
      // Update state month to match the saved budget
      state.budgetMonth = parseInt(m);
      state.budgetYear  = parseInt(y);
      loadBudgets();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // Month navigation
  document.getElementById("budgetPrevMonth").addEventListener("click", () => {
    let { budgetMonth: m, budgetYear: y } = state;
    m--; if (m < 1) { m = 12; y--; }
    state.budgetMonth = m; state.budgetYear = y;
    loadBudgets();
  });

  document.getElementById("budgetNextMonth").addEventListener("click", () => {
    let { budgetMonth: m, budgetYear: y } = state;
    m++; if (m > 12) { m = 1; y++; }
    state.budgetMonth = m; state.budgetYear = y;
    loadBudgets();
  });
});

function escBudget(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
