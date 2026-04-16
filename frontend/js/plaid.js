/**
 * plaid.js — Plaid Link sandbox connection flow.
 *
 * Flow:
 *   1. User clicks "Connect test bank".
 *   2. We call /api/plaid/link-token to get a short-lived token from our backend.
 *   3. We open Plaid Link with that token.
 *   4. User authenticates against a sandbox bank (credentials below).
 *   5. Plaid Link returns a one-time public_token via onSuccess.
 *   6. We POST the public_token to /api/plaid/exchange-token.
 *   7. Backend exchanges it for a permanent access_token, syncs accounts +
 *      transactions, and returns counts.
 *   8. Dashboard refreshes to show the imported data.
 *
 * Sandbox test credentials (Plaid provides these — no real bank needed):
 *   Username : user_good
 *   Password : pass_good
 *   (On the MFA screen just click "Get code" and use any value)
 */

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("connectBankBtn");
  if (!btn) return;

  btn.addEventListener("click", handleConnectClick);
});

async function handleConnectClick() {
  const btn = document.getElementById("connectBankBtn");

  // ── Guard: Plaid Link SDK must be present ─────────────────────────────
  if (typeof Plaid === "undefined") {
    showToast(
      "Plaid Link SDK failed to load. Check your internet connection and try again.",
      "error"
    );
    return;
  }

  _setBtnLoading(btn, true);

  let handler = null;

  try {
    // ── Step 1: get link token from our backend ──────────────────────────
    let tokenData;
    try {
      tokenData = await api.plaidLinkToken();
    } catch (err) {
      // Backend returns 503 when Plaid is not configured — surface it clearly
      const isUnconfigured =
        err.message.includes("not configured") || err.message.includes("not installed");
      showToast(
        isUnconfigured
          ? "Plaid is not set up yet. Add PLAID_CLIENT_ID and PLAID_SECRET to your .env and restart."
          : `Could not start Plaid Link: ${err.message}`,
        "error"
      );
      return;
    }

    // ── Step 2: open Plaid Link ──────────────────────────────────────────
    handler = Plaid.create({
      token: tokenData.link_token,

      onSuccess: async (publicToken, metadata) => {
        _setBtnLoading(btn, true, "Importing…");
        try {
          // ── Step 3: exchange token + sync on the backend ───────────────
          const result = await api.plaidExchangeToken(publicToken);
          showToast(
            `Connected! Imported ${result.accounts_imported} account(s) and ` +
            `${result.transactions_imported} transaction(s).`,
            "success"
          );
          // Refresh shared state and dashboard so new accounts/transactions appear
          await loadSharedData();
          if (window.state && state.currentPage === "dashboard") {
            loadDashboard();
          }
        } catch (err) {
          showToast(`Import failed: ${err.message}`, "error");
        } finally {
          _resetBtn(btn);
        }
      },

      onExit: (err, metadata) => {
        if (err) {
          // err is null for normal user-initiated exits
          showToast("Connection cancelled.", "");
        }
        _resetBtn(btn);
      },

      onEvent: (eventName, metadata) => {
        // Useful for debugging the Link flow during development
        console.debug("[Plaid Link event]", eventName, metadata);
      },
    });

    handler.open();

  } catch (err) {
    showToast(`Unexpected error: ${err.message}`, "error");
    _resetBtn(btn);
  }
}

// ── Button state helpers ───────────────────────────────────────────────────

function _setBtnLoading(btn, loading, label = "Connecting…") {
  btn.disabled = loading;
  btn.innerHTML = loading
    ? `<i data-feather="loader"></i> ${label}`
    : `<i data-feather="link-2"></i> Connect test bank`;
  if (window.feather) feather.replace();
}

function _resetBtn(btn) {
  _setBtnLoading(btn, false);
}
