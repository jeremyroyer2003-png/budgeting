"""
wealthica_provider.py — Wealthica integration stub.

Wealthica specialises in Canadian investment accounts: Wealthsimple, Questrade,
RBC Direct Investing, Mackenzie, Sun Life, iA Financial, etc.

SETUP (when you have credentials):
  1. Create an app at https://app.wealthica.com/developers
  2. Set WEALTHICA_CLIENT_ID in environment
  3. Set WEALTHICA_SECRET   in environment
  4. Replace the NotImplementedError bodies below with real API calls.

Wealthica API docs: https://wealthica.com/api/
"""

from datetime import date
from .base_provider import BaseProvider, RemoteAccount, RemoteTransaction


class WealthicaProvider(BaseProvider):
    """
    Wealthica adapter — implements the BaseProvider interface.
    Stub: raises NotImplementedError until credentials are available.
    """

    def authenticate(self, credentials: dict) -> None:
        self._client_id = credentials.get("client_id", "")
        self._secret    = credentials.get("secret", "")

    def get_accounts(self, user_token: str) -> list[RemoteAccount]:
        """
        Wealthica: GET /api/institutions + /api/positions
        Returns portfolio positions and account values.
        """
        _require_credentials(self._client_id)
        raise NotImplementedError(
            "WealthicaProvider.get_accounts() — set WEALTHICA_CLIENT_ID and implement."
        )

    def get_transactions(
        self,
        user_token: str,
        account_id: str | None,
        start_date: date,
        end_date: date,
    ) -> list[RemoteTransaction]:
        """
        Wealthica: GET /api/transactions?from=YYYY-MM-DD&to=YYYY-MM-DD
        """
        _require_credentials(self._client_id)
        raise NotImplementedError(
            "WealthicaProvider.get_transactions() — set WEALTHICA_CLIENT_ID and implement."
        )


def _require_credentials(client_id: str) -> None:
    if not client_id:
        raise RuntimeError(
            "Wealthica is not configured. "
            "Set WEALTHICA_CLIENT_ID and WEALTHICA_SECRET "
            "in your environment, then restart the backend."
        )
