"""
provider_router.py — Selects the right financial provider for an institution
and returns a ready-to-use provider instance.

Usage:
    from .provider_router import ProviderRouter

    router = ProviderRouter(app_config)
    provider = router.get_provider("desjardins")   # returns FlinksProvider
    provider = router.get_provider("chase")        # returns PlaidProvider
    provider = router.get_provider("questrade")    # returns WealthicaProvider
"""

from .institution_registry import get_institution, Institution
from .base_provider import BaseProvider
from .plaid_provider import PlaidProvider, PLAID_AVAILABLE


class ProviderUnavailableError(Exception):
    """Raised when the required provider SDK is not installed or not configured."""


class ProviderRouter:
    """
    Resolves institution_id → provider instance.

    Checks whether the primary provider is available (SDK installed + credentials
    present). Falls back to the secondary provider if the primary is not usable.
    """

    def __init__(self, config: dict):
        """
        config keys used:
          PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV
          FLINKS_API_URL, FLINKS_CLIENT_ID
          WEALTHICA_CLIENT_ID, WEALTHICA_SECRET
        """
        self._config = config

    # ── Public API ─────────────────────────────────────────────────────────

    def get_provider(self, institution_id: str) -> BaseProvider:
        """
        Return an authenticated provider instance for the given institution.
        Raises ProviderUnavailableError if neither primary nor fallback is usable.
        """
        inst = get_institution(institution_id)
        if inst is None:
            # Unknown institution — default to Plaid and hope for the best
            return self._build_provider("plaid", institution_id)

        for provider_name in _provider_order(inst):
            if self._is_available(provider_name):
                return self._build_provider(provider_name, institution_id)

        raise ProviderUnavailableError(
            f"No configured provider available for '{institution_id}'. "
            f"Tried: {inst.provider}" +
            (f", {inst.fallback}" if inst.fallback else "") + ". "
            "Set the required environment variables to enable the provider."
        )

    def provider_for_institution(self, institution_id: str) -> str:
        """
        Return the name of the provider that would be selected (without building it).
        Useful for the frontend to know which Link UI to launch.
        """
        inst = get_institution(institution_id)
        if inst is None:
            return "plaid"
        for name in _provider_order(inst):
            if self._is_available(name):
                return name
        return inst.provider  # return primary even if unavailable (caller decides)

    # ── Provider availability checks ───────────────────────────────────────

    def _is_available(self, provider_name: str) -> bool:
        if provider_name == "plaid":
            return (
                PLAID_AVAILABLE
                and bool(self._config.get("PLAID_CLIENT_ID"))
                and bool(self._config.get("PLAID_SECRET"))
            )
        if provider_name == "flinks":
            return bool(self._config.get("FLINKS_API_URL"))
        if provider_name == "wealthica":
            return bool(self._config.get("WEALTHICA_CLIENT_ID"))
        return False

    # ── Provider factory ───────────────────────────────────────────────────

    def _build_provider(self, provider_name: str, institution_id: str) -> BaseProvider:
        if provider_name == "plaid":
            from .plaid_provider import PlaidProvider, build_plaid_client
            p = PlaidProvider()
            p.authenticate({
                "client_id": self._config["PLAID_CLIENT_ID"],
                "secret":    self._config["PLAID_SECRET"],
                "env":       self._config.get("PLAID_ENV", "sandbox"),
            })
            return p

        if provider_name == "flinks":
            from .flinks_provider import FlinksProvider
            p = FlinksProvider()
            p.authenticate({
                "api_url":   self._config["FLINKS_API_URL"],
                "client_id": self._config.get("FLINKS_CLIENT_ID", ""),
            })
            return p

        if provider_name == "wealthica":
            from .wealthica_provider import WealthicaProvider
            p = WealthicaProvider()
            p.authenticate({
                "client_id": self._config["WEALTHICA_CLIENT_ID"],
                "secret":    self._config.get("WEALTHICA_SECRET", ""),
            })
            return p

        raise ProviderUnavailableError(f"Unknown provider: {provider_name}")


def _provider_order(inst: Institution) -> list[str]:
    """Return [primary, fallback] with None filtered out."""
    order = [inst.provider]
    if inst.fallback:
        order.append(inst.fallback)
    return order
