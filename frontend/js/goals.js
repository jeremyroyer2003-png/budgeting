/**
 * goals.js — Goal cards with progress, on-track indicators, and add/edit.
 */

let _editingGoalId = null;

async function loadGoals() {
  try {
    const goals = await api.getGoals();
    renderGoalCards(goals);
  } catch (err) {
    document.getElementById("goalCards").innerHTML =
      `<div class="empty-state">Error loading goals.</div>`;
    showToast(err.message, "error");
  }
}

function renderGoalCards(goals) {
  const container = document.getElementById("goalCards");
  if (!goals.length) {
    container.innerHTML = `
      <div class="empty-state">
        No financial goals yet.<br>
        <br><button class="btn btn-primary" onclick="openGoalModal()"><i data-feather="plus"></i> Create a goal</button>
      </div>`;
    if (window.feather) feather.replace();
    return;
  }

  container.innerHTML = goals.map(g => {
    const pct      = g.progress_pct;
    const ghostPct = g.ghost_pct != null ? Math.min(g.ghost_pct, 100) : null;

    // Fill colour: complete → green, behind ghost → orange, otherwise green
    let fillClass = "no-data";
    if (pct >= 100)                            fillClass = "complete";
    else if (ghostPct != null && pct < ghostPct) fillClass = "behind";
    else                                         fillClass = "on-track";

    const onTrackEl = buildOnTrackChip(g);

    let metaHtml = "";
    if (g.monthly_target) {
      metaHtml += `<span>Monthly target: <strong>${fmtCurrency(g.monthly_target)}</strong></span>`;
    }
    if (g.target_date) {
      metaHtml += `<span>By: <strong>${fmtDate(g.target_date)}</strong></span>`;
    }
    if (g.months_left != null) {
      metaHtml += `<span>${g.months_left} month${g.months_left !== 1 ? "s" : ""} left</span>`;
    }
    if (g.needed_per_month != null && g.on_track === false) {
      metaHtml += `<span style="color:var(--danger)">Need <strong>${fmtCurrency(g.needed_per_month)}/mo</strong> to stay on track</span>`;
    }

    // Time-to-goal headline
    const timeHeadline = buildTimeHeadline(g);
    // Actionable gap
    const actionableGap = buildActionableGap(g);

    return `
      <div class="goal-card">
        <div class="goal-card-header">
          <span class="goal-title">${escGoal(g.name)}</span>
          <span class="goal-type-tag ${g.type}">${goalTypeLabel(g.type)}</span>
        </div>

        ${timeHeadline}

        <div class="goal-amounts-row">
          <div class="goal-current">${fmtCurrency(g.current_amount)}</div>
          <div class="goal-of-total">of ${fmtCurrency(g.target_amount)}</div>
        </div>

        <!-- 3-layer Ghost Bar -->
        <div class="goal-progress-track">
          ${ghostPct != null
            ? `<div class="goal-progress-ghost" style="width:${ghostPct}%"></div>`
            : ""}
          <div class="goal-progress-fill ${fillClass}" style="width:${Math.min(pct, 100)}%"></div>
        </div>
        <div class="goal-pct-row">
          <span class="goal-pct-label">${pct}% complete</span>
          ${ghostPct != null ? `<span class="goal-ghost-label">Target pace: ${Math.round(ghostPct)}%</span>` : ""}
        </div>

        ${actionableGap}
        ${buildVelocityInsight(g)}

        <div class="goal-meta">${metaHtml}</div>

        ${onTrackEl}

        ${g.notes ? `<div style="font-size:12px;color:var(--text-secondary);margin-top:4px">${escGoal(g.notes)}</div>` : ""}

        <div class="goal-actions">
          <button class="btn btn-ghost btn-sm" onclick="openEditGoalModal(${g.id})">
            <i data-feather="edit-2"></i> Edit
          </button>
          <button class="btn btn-ghost btn-sm" onclick="deleteGoal(${g.id})" style="color:var(--danger)">
            <i data-feather="trash-2"></i>
          </button>
        </div>
      </div>
    `;
  }).join("");
  if (window.feather) feather.replace();
}

function buildVelocityInsight(g) {
  if (!g.projected_completion) {
    if (g.velocity_30d != null && g.velocity_30d <= 0) {
      return `<div class="goal-velocity">No savings activity detected in the last 30 days.</div>`;
    }
    return "";
  }

  const projDate  = new Date(g.projected_completion + "T00:00:00");
  const projLabel = projDate.toLocaleDateString("en-CA", { month: "long", year: "numeric" });
  const pace      = fmtCurrency(g.velocity_30d);
  const diff      = g.projected_months_diff;

  let scheduleHtml = "";
  if (diff != null) {
    const absDiff = Math.abs(diff);
    const months  = absDiff < 1 ? "less than a month" : `${Math.round(absDiff)} month${Math.round(absDiff) !== 1 ? "s" : ""}`;
    if (diff > 0.5) {
      scheduleHtml = ` — <span class="behind">${months} late</span>`;
    } else if (diff < -0.5) {
      scheduleHtml = ` — <span class="ahead">${months} early</span>`;
    } else {
      scheduleHtml = ` — <span class="ahead">right on schedule</span>`;
    }
  }

  return `
    <div class="goal-velocity">
      Saving <strong>${pace}</strong> over last 30 days.
      At this pace, you'll reach your goal by <strong>${projLabel}</strong>${scheduleHtml}.
    </div>`;
}

function buildOnTrackChip(g) {
  if (g.on_track === true) {
    return `<span class="on-track-chip yes"><i data-feather="check-circle"></i> On track</span>`;
  } else if (g.on_track === false) {
    return `<span class="on-track-chip no"><i data-feather="alert-circle"></i> At risk</span>`;
  }
  return "";
}

function buildTimeHeadline(g) {
  if (g.progress_pct >= 100) {
    return `<div class="goal-time-headline complete">🎉 Goal reached!</div>`;
  }
  if (g.projected_completion) {
    const projDate  = new Date(g.projected_completion + "T00:00:00");
    const now       = new Date();
    const msLeft    = projDate - now;
    const daysLeft  = Math.ceil(msLeft / 86400000);
    const label     = projDate.toLocaleDateString("en-CA", { month: "long", year: "numeric" });
    if (daysLeft <= 30) {
      return `<div class="goal-time-headline urgent">Almost there — ${daysLeft} day${daysLeft !== 1 ? "s" : ""} to go</div>`;
    }
    const monthsLeft = Math.round(daysLeft / 30.44);
    const diffLabel  = g.projected_months_diff != null && Math.abs(g.projected_months_diff) > 0.5
      ? (g.projected_months_diff > 0
          ? ` <span class="behind">(${Math.round(g.projected_months_diff)}mo late)</span>`
          : ` <span class="ahead">(${Math.abs(Math.round(g.projected_months_diff))}mo early)</span>`)
      : "";
    return `<div class="goal-time-headline">On track for <strong>${label}</strong>${diffLabel} · ${monthsLeft} month${monthsLeft !== 1 ? "s" : ""} away</div>`;
  }
  if (g.months_left != null) {
    return `<div class="goal-time-headline">${g.months_left} month${g.months_left !== 1 ? "s" : ""} to target date</div>`;
  }
  return "";
}

function buildActionableGap(g) {
  if (g.progress_pct >= 100) return "";
  const remaining = g.target_amount - g.current_amount;
  if (remaining <= 0) return "";

  // If behind pace, show exactly how much more per month is needed
  if (g.on_track === false && g.needed_per_month != null && g.monthly_target != null) {
    const gap = g.needed_per_month - g.monthly_target;
    if (gap > 0) {
      return `<div class="goal-gap-callout">
        <i data-feather="alert-circle"></i>
        Add <strong>${fmtCurrency(gap)}/month</strong> to get back on track
        — you need ${fmtCurrency(g.needed_per_month)}/mo total
      </div>`;
    }
  }

  // If no monthly target set
  if (!g.monthly_target && g.months_left != null && g.months_left > 0) {
    const suggested = Math.ceil(remaining / g.months_left);
    return `<div class="goal-gap-callout info">
      <i data-feather="info"></i>
      Save <strong>${fmtCurrency(suggested)}/month</strong> to reach your target on time
    </div>`;
  }

  return "";
}

function goalTypeLabel(type) {
  return { savings: "Savings", investment: "Investment", debt_payoff: "Debt Payoff", purchase: "Purchase" }[type] || type;
}

// ---- Modals ----
function openGoalModal() {
  _editingGoalId = null;
  document.getElementById("goalModalTitle").textContent = "New Goal";
  document.getElementById("goalForm").reset();
  document.getElementById("goalId").value = "";
  openModal("goalModal");
}

async function openEditGoalModal(goalId) {
  _editingGoalId = goalId;
  try {
    const goals = await api.getGoals();
    const g = goals.find(x => x.id === goalId);
    if (!g) { showToast("Goal not found.", "error"); return; }

    document.getElementById("goalModalTitle").textContent = "Edit Goal";
    document.getElementById("goalId").value       = g.id;
    document.getElementById("goalName").value     = g.name;
    document.getElementById("goalType").value     = g.type;
    document.getElementById("goalTarget").value   = g.target_amount;
    document.getElementById("goalCurrent").value  = g.current_amount;
    document.getElementById("goalMonthly").value  = g.monthly_target || "";
    document.getElementById("goalDate").value     = g.target_date || "";
    document.getElementById("goalNotes").value    = g.notes || "";
    openModal("goalModal");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteGoal(goalId) {
  confirmDelete("Archive this goal?", async () => {
    try {
      await api.deleteGoal(goalId);
      showToast("Goal archived.", "success");
      loadGoals();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("addGoalBtn").addEventListener("click", openGoalModal);

  document.getElementById("goalForm").addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
      name:           document.getElementById("goalName").value,
      type:           document.getElementById("goalType").value,
      target_amount:  parseFloat(document.getElementById("goalTarget").value),
      current_amount: parseFloat(document.getElementById("goalCurrent").value) || 0,
      monthly_target: parseFloat(document.getElementById("goalMonthly").value) || null,
      target_date:    document.getElementById("goalDate").value || null,
      notes:          document.getElementById("goalNotes").value,
    };

    try {
      if (_editingGoalId) {
        await api.updateGoal(_editingGoalId, payload);
        showToast("Goal updated.", "success");
      } else {
        await api.createGoal(payload);
        showToast("Goal created.", "success");
      }
      closeModal("goalModal");
      loadGoals();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
});

function escGoal(str) {
  return String(str || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
