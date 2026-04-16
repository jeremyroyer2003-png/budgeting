"""
Integration layer for external financial data providers.

Current providers:
  - mock  : Fake data for local development and demos
  - plaid : Sandbox / production bank sync via Plaid API

To add a new provider (e.g. Flinks):
  1. Create flinks_provider.py implementing BaseProvider
  2. Import it below and add to PROVIDERS
  3. Add any new routes to routes/plaid.py as a reference

Provider availability:
  - mock  : always available (no credentials needed)
  - plaid : available when plaid-python is installed AND
            PLAID_CLIENT_ID + PLAID_SECRET env vars are set
"""

from .base_provider import BaseProvider
from .mock_provider import MockProvider

PROVIDERS: dict[str, type[BaseProvider]] = {
    "mock": MockProvider,
}

# Plaid is registered only when the SDK is installed.
# Install with: pip install plaid-python
from .plaid_provider import PlaidProvider, PLAID_AVAILABLE
if PLAID_AVAILABLE:
    PROVIDERS["plaid"] = PlaidProvider

# Future providers follow the same pattern:
# from .flinks_provider import FlinksProvider, FLINKS_AVAILABLE
# if FLINKS_AVAILABLE:
#     PROVIDERS["flinks"] = FlinksProvider


def get_provider(name: str) -> BaseProvider:
    cls = PROVIDERS.get(name)
    if not cls:
        raise ValueError(f"Unknown provider: {name!r}. Available: {list(PROVIDERS)}")
    return cls()
