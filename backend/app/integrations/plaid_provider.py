"""
Plaid provider — implements BaseProvider using the Plaid API.

Supports sandbox, development, and production environments via PLAID_ENV.
Sandbox credentials (for testing without real bank accounts):
    Username: user_good
    Password: pass_good

PRODUCTION CHECKLIST (before going live):
  [ ] Switch PLAID_ENV to "production"
  [ ] Encrypt access_token at rest in PlaidConnection (use a secrets manager)
  [ ] Handle Plaid webhooks for real-time transaction updates
  [ ] Implement cursor-based /transactions/sync instead of date-range fetching
  [ ] Add rate-limit handling and retry logic with exponential back-off
  [ ] Request only the Plaid products your app actually uses
"""

from datetime import date, timedelta
from typing import Optional

from .base_provider import BaseProvider, RemoteAccount, RemoteTransaction

# Guard: the app runs normally if plaid-python is not installed.
# Install it with: pip install plaid-python
try:
    import plaid
    from plaid.api import plaid_api
    from plaid.model.accounts_get_request import AccountsGetRequest
    from plaid.model.transactions_get_request import TransactionsGetRequest
    from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
    PLAID_AVAILABLE = True
except ImportError:
    PLAID_AVAILABLE = False


# ── Plaid → app account-type mapping ──────────────────────────────────────
# Plaid type/subtype strings → our Account.type values
_ACCOUNT_TYPE_MAP: dict[tuple[str, str], str] = {
    ("depository", "checking"):    "checking",
    ("depository", "savings"):     "savings",
    ("depository", "cd"):          "savings",
    ("depository", "money market"):"savings",
    ("credit",     "credit card"): "credit",
    ("investment", "brokerage"):   "investment",
    ("investment", "ira"):         "investment",
    ("investment", "401k"):        "investment",
    ("investment", "roth"):        "investment",
}

def _map_account_type(plaid_type: str, plaid_subtype: Optional[str]) -> str:
    key = (plaid_type.lower(), (plaid_subtype or "").lower())
    if key in _ACCOUNT_TYPE_MAP:
        return _ACCOUNT_TYPE_MAP[key]
    # Fallback on the top-level type alone
    fallback = {"depository": "checking", "credit": "credit", "investment": "investment"}
    return fallback.get(plaid_type.lower(), "checking")


# ── Plaid category → our Category name hint ────────────────────────────────
# Plaid returns categories as a list, e.g. ["Food and Drink", "Restaurants"].
# We map the first element to one of our seeded category names.
_CATEGORY_MAP: dict[str, str] = {
    "food and drink":            "Food & Dining",
    "restaurants":               "Food & Dining",
    "groceries":                 "Food & Dining",
    "travel":                    "Travel",
    "transportation":            "Transportation",
    "taxi":                      "Transportation",
    "shops":                     "Shopping",
    "recreation":                "Entertainment",
    "entertainment":             "Entertainment",
    "healthcare":                "Healthcare",
    "medical":                   "Healthcare",
    "service":                   "Utilities",
    "utilities":                 "Utilities",
    "payment":                   "Savings Transfer",
    "transfer":                  "Savings Transfer",
    "bank fees":                 "Utilities",
    "community":                 "Entertainment",
    "education":                 "Education",
    "personal care":             "Personal Care",
}

def _category_hint(plaid_categories: Optional[list]) -> Optional[str]:
    """Return our category name for the best-matching Plaid category."""
    if not plaid_categories:
        return None
    for cat in plaid_categories:
        mapped = _CATEGORY_MAP.get(cat.lower())
        if mapped:
            return mapped
    return None


def build_plaid_client(client_id: str, secret: str, env: str):
    """Construct an authenticated PlaidApi client."""
    if not PLAID_AVAILABLE:
        raise RuntimeError("plaid-python is not installed. Run: pip install plaid-python")

    env_map = {
        "sandbox":     plaid.Environment.Sandbox,
        "development": plaid.Environment.Development,
        "production":  plaid.Environment.Production,
    }
    configuration = plaid.Configuration(
        host=env_map.get(env, plaid.Environment.Sandbox),
        api_key={"clientId": client_id, "secret": secret},
    )
    return plaid_api.PlaidApi(plaid.ApiClient(configuration))


class PlaidProvider(BaseProvider):
    """
    Fetches accounts and transactions from Plaid using a stored access_token.

    Usage:
        provider = PlaidProvider()
        provider.authenticate({"client_id": ..., "secret": ..., "env": "sandbox"})
        accounts = provider.get_accounts(access_token)
        txns     = provider.get_transactions(access_token, None, start, end)
    """

    def __init__(self):
        self._client = None

    def authenticate(self, credentials: dict) -> None:
        self._client = build_plaid_client(
            credentials["client_id"],
            credentials["secret"],
            credentials.get("env", "sandbox"),
        )

    def get_accounts(self, user_token: str) -> list[RemoteAccount]:
        """Return all accounts for the given Plaid access_token."""
        resp = self._client.accounts_get(AccountsGetRequest(access_token=user_token))
        results = []
        for acct in resp.accounts:
            plaid_type    = str(acct.type.value)    if acct.type    else "depository"
            plaid_subtype = str(acct.subtype.value) if acct.subtype else None
            results.append(RemoteAccount(
                provider_account_id   = acct.account_id,
                name                  = acct.name,
                type                  = _map_account_type(plaid_type, plaid_subtype),
                balance               = float(acct.balances.current or 0.0),
                institution           = "",   # populated by the caller from ItemGetResponse
                account_number_last4  = acct.mask,
            ))
        return results

    def get_transactions(
        self,
        user_token: str,
        account_id: Optional[str],
        start_date: date,
        end_date: date,
    ) -> list[RemoteTransaction]:
        """
        Return transactions for the given access_token over the date range.

        If account_id is None, transactions for all accounts are returned.

        PRODUCTION NOTE: Replace with /transactions/sync (cursor-based) for
        real-time updates and efficient incremental fetching.
        """
        options_kwargs = {}
        if account_id:
            options_kwargs["account_ids"] = [account_id]

        req = TransactionsGetRequest(
            access_token=user_token,
            start_date=start_date,
            end_date=end_date,
            options=TransactionsGetRequestOptions(**options_kwargs) if options_kwargs else TransactionsGetRequestOptions(),
        )
        resp = self._client.transactions_get(req)
        results = []
        for tx in resp.transactions:
            # Plaid amount: positive = outflow (expense), negative = inflow (income)
            if tx.amount >= 0:
                tx_type = "expense"
                amount  = float(tx.amount)
            else:
                tx_type = "income"
                amount  = float(abs(tx.amount))

            results.append(RemoteTransaction(
                provider_transaction_id = tx.transaction_id,
                provider_account_id     = tx.account_id,
                amount                  = amount,
                type                    = tx_type,
                description             = tx.name or "",
                date                    = tx.date,
                category_hint           = _category_hint(tx.category),
            ))
        return results
