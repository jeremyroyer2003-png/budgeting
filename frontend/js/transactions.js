/**
 * transactions.js — Transaction list, add/edit/delete.
 */

let _editingTxId = null;

async function loadTransactions() {
  const params = {};
  const type = document.getElementById("txTypeFilter").value;
  const cat  = document.getElementById("txCategoryFilter").value;
  const mon  = document.getElementById("txMonthFilter").value; // "YYYY-MM"

  if (type) params.type = type;
  if (cat)  params.category_id = cat;
  if (mon) {
    const [y, m] = mon.split("-");
    params.month = m;
    params.year  = y;
  }

  renderTxLoading();
  try {
    const txns = await api.getTransactions(params);
    renderTransactions(txns);
  } catch (err) {
    document.getElementById("txBody").innerHTML =
      `<tr><td colspan="6" class="empty-cell">Error loading transactions.</td></tr>`;
    showToast(err.message, "error");
  }
}

function renderTxLoading() {
  document.getElementById("txBody").innerHTML =
    `<tr><td colspan="6" class="empty-cell">Loading…</td></tr>`;
}

function renderTransactions(txns) {
  const tbody = document.getElementById("txBody");
  if (!txns.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-cell">No transactions found.</td></tr>`;
    return;
  }
  tbody.innerHTML = txns.map(t => {
    const isIncome = t.type === "income";
    const amtClass = isIncome ? "amount-income" : "amount-expense";
    const sign     = isIncome ? "+" : "−";
    const catColor = t.category_color || "#94A3B8";
    return `
      <tr>
        <td class="tx-date">${fmtDate(t.date)}</td>
        <td class="tx-desc">${escHtml(t.description || "—")}</td>
        <td>
          ${t.category_name
            ? `<span class="cat-pill"><span class="cat-dot" style="background:${catColor}"></span>${escHtml(t.category_name)}</span>`
            : "—"}
        </td>
        <td class="tx-account">${escHtml(t.account_name || "—")}</td>
        <td class="text-right ${amtClass}">${sign}${fmtCurrency(t.amount)}</td>
        <td class="text-right">
          <button class="btn-icon" title="Edit"    onclick="openEditTxModal(${t.id})"><i data-feather="edit-2"></i></button>
          <button class="btn-icon" title="Delete"  onclick="deleteTx(${t.id})"><i data-feather="trash-2"></i></button>
        </td>
      </tr>
    `;
  }).join("");
  if (window.feather) feather.replace();
}

// ---- Category select — tx modal only ----
// Targets only #txCategory (not the shared budget/filter selects).
// Always filters by the given type so only relevant categories are shown.
function populateTxCategorySelect(type) {
  const sel = document.getElementById("txCategory");
  if (!sel) {
    console.warn("[transactions] #txCategory element not found in DOM");
    return;
  }

  const prev = sel.value;
  sel.innerHTML = '<option value="">— Select —</option>';

  const cats = (state.categories || []).filter(c => c.type === type);
  if (!cats.length) {
    console.warn(`[transactions] No categories for type="${type}". ` +
      `state.categories has ${(state.categories || []).length} entries:`, state.categories);
  }

  cats.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.textContent = c.name;
    sel.appendChild(opt);
  });

  // Restore previous selection only if it's still in the filtered list
  if (prev && sel.querySelector(`option[value="${prev}"]`)) {
    sel.value = prev;
  }
}

// ---- Add Transaction Modal ----
function openAddTxModal() {
  _editingTxId = null;
  document.getElementById("txModalTitle").textContent = "Add Transaction";
  document.getElementById("txId").value = "";
  document.getElementById("txForm").reset();
  document.getElementById("txDate").value = new Date().toISOString().slice(0, 10);

  // Determine type from radio (form.reset() restores HTML default: "expense")
  const checked = document.querySelector("input[name='txType']:checked");
  const type = checked ? checked.value : "expense";
  populateTxCategorySelect(type);

  populateAccountSelects();

  // Default to first account
  if (state.accounts.length) {
    document.getElementById("txAccount").value = state.accounts[0].id;
  }

  // Re-filter categories when type radio changes
  bindTxTypeChange();
  openModal("txModal");
}

async function openEditTxModal(txId) {
  _editingTxId = txId;
  try {
    const tx = await api.getTransaction(txId);
    document.getElementById("txModalTitle").textContent = "Edit Transaction";
    document.getElementById("txId").value = tx.id;

    // Set type radio first so the category list is filtered correctly
    document.querySelector(`input[name="txType"][value="${tx.type}"]`).checked = true;
    document.getElementById("txAmount").value = tx.amount;
    document.getElementById("txDate").value = tx.date;
    document.getElementById("txDescription").value = tx.description || "";

    // Populate categories filtered to this tx's type, then set the saved value
    populateTxCategorySelect(tx.type);
    document.getElementById("txCategory").value = tx.category_id || "";

    populateAccountSelects();
    document.getElementById("txAccount").value = tx.account_id || "";

    bindTxTypeChange();
    openModal("txModal");
  } catch (err) {
    showToast("Could not load transaction.", "error");
  }
}

function bindTxTypeChange() {
  // onchange assignment naturally replaces any prior handler — no stacking on repeated opens
  document.querySelectorAll("input[name='txType']").forEach(radio => {
    radio.onchange = () => populateTxCategorySelect(radio.value);
  });
}

async function deleteTx(txId) {
  confirmDelete("Delete this transaction? This cannot be undone.", async () => {
    try {
      await api.deleteTransaction(txId);
      showToast("Transaction deleted.", "success");
      loadTransactions();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

// ---- Form submit ----
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("txForm").addEventListener("submit", async e => {
    e.preventDefault();
    const type     = document.querySelector("input[name='txType']:checked").value;
    const amount   = parseFloat(document.getElementById("txAmount").value);
    const date     = document.getElementById("txDate").value;
    const desc     = document.getElementById("txDescription").value;
    const catId    = parseInt(document.getElementById("txCategory").value) || null;
    const accId    = parseInt(document.getElementById("txAccount").value);

    if (!accId) { showToast("Please select an account.", "error"); return; }

    const payload = { account_id: accId, category_id: catId, amount, type, description: desc, date };

    try {
      if (_editingTxId) {
        await api.updateTransaction(_editingTxId, payload);
        showToast("Transaction updated.", "success");
      } else {
        await api.createTransaction(payload);
        showToast("Transaction added.", "success");
      }
      closeModal("txModal");
      if (state.currentPage === "transactions") loadTransactions();
      if (state.currentPage === "dashboard")    loadDashboard();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  document.getElementById("addTxBtn").addEventListener("click", openAddTxModal);

  // Filters
  ["txTypeFilter", "txCategoryFilter", "txMonthFilter"].forEach(id => {
    document.getElementById(id).addEventListener("change", loadTransactions);
  });

  // Default month filter to current month
  const today = new Date();
  document.getElementById("txMonthFilter").value =
    `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
});

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
