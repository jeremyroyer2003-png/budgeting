"""
flinks_provider.py — Flinks integration stub.

Flinks covers Canadian banks with higher reliability than Plaid for
institutions like Desjardins, CIBC, BMO, and credit unions.

SETUP (when you have credentials):
  1. Set FLINKS_API_URL  in environment  (e.g. https://sandbox.flinks.com/v3)
  2. Set FLINKS_CLIENT_ID in environment
  3. Replace the NotImplementedError bodies below with real API calls.

Flinks API docs: https://docs.flinks.com
"""

from datetime import date
from .base_provider import BaseProvider, RemoteAccount, RemoteTransaction


class FlinksProvider(BaseProvider):
    """
    Flinks adapter — implements the BaseProvider interface.
    Stub: raises NotImplementedError until credentials are available.
    """

    def authenticate(self, credentials: dict) -> None:
        self._api_url   = credentials.get("api_url", "")
        self._client_id = credentials.get("client_id", "")

    def get_accounts(self, user_token: str) -> list[RemoteAccount]:
        """
        Flinks equivalent: GET /v3/{loginRequestId}/GetAccountsDetail
        Returns account balances and metadata.
        """
        _require_credentials(self._api_url)
        raise NotImplementedError(
            "FlinksProvider.get_accounts() — set FLINKS_API_URL and implement."
        )

    def get_transactions(
        self,
        user_token: str,
        account_id: str | None,
        start_date: date,
        end_date: date,
    ) -> list[RemoteTransaction]:
        """
        Flinks equivalent: POST /v3/{loginRequestId}/GetAccountsDetail
        with Transactions included in the payload.
        """
        _require_credentials(self._api_url)
        raise NotImplementedError(
            "FlinksProvider.get_transactions() — set FLINKS_API_URL and implement."
        )


def _require_credentials(api_url: str) -> None:
    if not api_url:
        raise RuntimeError(
            "Flinks is not configured. "
            "Set FLINKS_API_URL (and optionally FLINKS_CLIENT_ID) "
            "in your environment, then restart the backend."
        )
