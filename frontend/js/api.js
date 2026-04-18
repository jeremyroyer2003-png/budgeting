/**
 * api.js — Thin wrapper around fetch() for the ClearBudget REST API.
 *
 * All methods return Promises that resolve to the parsed JSON body.
 * On non-2xx responses, they throw an Error with a readable message.
 */

const API_BASE = "http://localhost:5000/api";

async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const token = window.getToken ? window.getToken() : null;
  const defaults = {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    },
  };
  const res = await fetch(url, { ...defaults, ...options, headers: { ...defaults.headers, ...(options.headers || {}) } });
  if (res.status === 401) {
    if (window.logout) window.logout();
    throw new Error("Session expired. Please log in again.");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

const api = {
  // --- Transactions ---
  getTransactions:  (params = {}) => apiFetch(`/transactions/?${new URLSearchParams(params)}`),
  getTransaction:   (id)          => apiFetch(`/transactions/${id}`),
  createTransaction:(data)        => apiFetch("/transactions/", { method: "POST", body: JSON.stringify(data) }),
  updateTransaction:(id, data)    => apiFetch(`/transactions/${id}`, { method: "PUT",  body: JSON.stringify(data) }),
  deleteTransaction:(id)          => apiFetch(`/transactions/${id}`, { method: "DELETE" }),

  // --- Categories ---
  getCategories:    ()            => apiFetch("/categories/"),
  createCategory:   (data)        => apiFetch("/categories/", { method: "POST", body: JSON.stringify(data) }),

  // --- Accounts ---
  getAccounts:      ()            => apiFetch("/accounts/"),
  createAccount:    (data)        => apiFetch("/accounts/", { method: "POST", body: JSON.stringify(data) }),

  // --- Budgets ---
  getBudgets:       (params = {}) => apiFetch(`/budgets/?${new URLSearchParams(params)}`),
  setBudget:        (data)        => apiFetch("/budgets/", { method: "POST", body: JSON.stringify(data) }),
  getBudgetSummary: (params = {}) => apiFetch(`/budgets/summary?${new URLSearchParams(params)}`),
  deleteBudget:     (id)          => apiFetch(`/budgets/${id}`, { method: "DELETE" }),

  // --- Goals ---
  getGoals:         ()            => apiFetch("/goals/"),
  createGoal:       (data)        => apiFetch("/goals/", { method: "POST", body: JSON.stringify(data) }),
  updateGoal:       (id, data)    => apiFetch(`/goals/${id}`, { method: "PUT",  body: JSON.stringify(data) }),
  deleteGoal:       (id)          => apiFetch(`/goals/${id}`, { method: "DELETE" }),

  // --- Alerts ---
  getAlerts:             (params = {}) => apiFetch(`/alerts/?${new URLSearchParams(params)}`),
  markAlertRead:         (id)          => apiFetch(`/alerts/${id}/read`, { method: "POST" }),
  markAllRead:           ()            => apiFetch("/alerts/read-all",       { method: "POST" }),
  generateAlerts:        ()            => apiFetch("/alerts/generate",       { method: "POST" }),
  getWeeklySummary:      ()            => apiFetch("/alerts/weekly-summary"),
  generateWeeklySummary: ()            => apiFetch("/alerts/generate-weekly",{ method: "POST" }),

  // --- Dashboard ---
  getDashboard:     (params = {}) => apiFetch(`/dashboard/?${new URLSearchParams(params)}`),

  // --- Subscriptions ---
  getSubscriptions: () => apiFetch("/subscriptions/"),

  // --- Plaid sandbox ---
  plaidLinkToken:    ()        => apiFetch("/plaid/link-token",    { method: "POST" }),
  plaidExchangeToken:(token)   => apiFetch("/plaid/exchange-token", {
    method: "POST",
    body: JSON.stringify({ public_token: token }),
  }),
  plaidSync:         ()        => apiFetch("/plaid/sync",          { method: "POST" }),
  plaidConnections:  ()        => apiFetch("/plaid/connections"),
  plaidDisconnect:   (id)      => apiFetch(`/plaid/connections/${id}`, { method: "DELETE" }),
};
