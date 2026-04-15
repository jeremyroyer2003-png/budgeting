"""
Abstract base class for financial data providers.

Every real provider (Plaid, Flinks, etc.) must implement this interface.
This keeps business logic decoupled from any single bank-sync service.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class RemoteAccount:
    provider_account_id: str
    name: str
    type: str           # checking, savings, investment, credit
    balance: float
    institution: str
    account_number_last4: Optional[str] = None


@dataclass
class RemoteTransaction:
    provider_transaction_id: str
    provider_account_id: str
    amount: float
    type: str           # income or expense
    description: str
    date: date
    category_hint: Optional[str] = None


class BaseProvider(ABC):
    """
    Implement this interface to connect a financial data source.

    Typical flow:
      1. Call authenticate() once with provider credentials.
      2. Call get_accounts() to fetch the user's accounts.
      3. Call get_transactions() for each account to pull history.
      4. Map RemoteAccount / RemoteTransaction onto local models.
    """

    @abstractmethod
    def authenticate(self, credentials: dict) -> None:
        """Store and validate the credentials for this provider session."""

    @abstractmethod
    def get_accounts(self, user_token: str) -> list[RemoteAccount]:
        """Return all accounts accessible with the given user token."""

    @abstractmethod
    def get_transactions(
        self,
        user_token: str,
        account_id: str,
        start_date: date,
        end_date: date,
    ) -> list[RemoteTransaction]:
        """Return transactions for a single account over the given date range."""
