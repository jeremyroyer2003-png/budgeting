"""
Integration layer for external financial data providers.

Current providers:
  - mock   : Fake data for local development and demos
  - plaid  : Stub ready for Plaid API credentials
  - flinks : Stub ready for Flinks API credentials

To add a new provider:
  1. Create a new file, e.g. my_bank_provider.py
  2. Subclass BaseProvider and implement all abstract methods
  3. Register it in PROVIDERS below
  4. Add an API route in routes/accounts.py to trigger a sync
"""

from .base_provider import BaseProvider
from .mock_provider import MockProvider

PROVIDERS: dict[str, type[BaseProvider]] = {
    "mock": MockProvider,
}

# Stubs for future providers — import only when credentials are configured
# from .plaid_provider import PlaidProvider
# from .flinks_provider import FlinksProvider
# PROVIDERS["plaid"] = PlaidProvider
# PROVIDERS["flinks"] = FlinksProvider


def get_provider(name: str) -> BaseProvider:
    cls = PROVIDERS.get(name)
    if not cls:
        raise ValueError(f"Unknown provider: {name!r}. Available: {list(PROVIDERS)}")
    return cls()
