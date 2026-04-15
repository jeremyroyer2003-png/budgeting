"""
Mock provider that returns realistic demo data without any real API calls.

Useful for local development, demos, and automated tests.
Replace with PlaidProvider or FlinksProvider for production.
"""

from datetime import date, timedelta
import random
from .base_provider import BaseProvider, RemoteAccount, RemoteTransaction


class MockProvider(BaseProvider):
    def authenticate(self, credentials: dict) -> None:
        # No real auth needed for the mock
        pass

    def get_accounts(self, user_token: str) -> list[RemoteAccount]:
        return [
            RemoteAccount(
                provider_account_id="mock-chk-001",
                name="Mock Chequing",
                type="checking",
                balance=4_250.00,
                institution="Demo Bank",
                account_number_last4="1234",
            ),
            RemoteAccount(
                provider_account_id="mock-sav-001",
                name="Mock Savings",
                type="savings",
                balance=12_000.00,
                institution="Demo Bank",
                account_number_last4="5678",
            ),
            RemoteAccount(
                provider_account_id="mock-inv-001",
                name="Mock Investment",
                type="investment",
                balance=28_500.00,
                institution="Demo Brokerage",
                account_number_last4="9012",
            ),
        ]

    def get_transactions(
        self,
        user_token: str,
        account_id: str,
        start_date: date,
        end_date: date,
    ) -> list[RemoteTransaction]:
        # Generate plausible fake transactions for the date range
        txns = []
        current = start_date
        while current <= end_date:
            if random.random() < 0.4:
                txns.append(RemoteTransaction(
                    provider_transaction_id=f"mock-{account_id}-{current.isoformat()}-{random.randint(1000, 9999)}",
                    provider_account_id=account_id,
                    amount=round(random.uniform(5, 200), 2),
                    type="expense",
                    description=random.choice([
                        "Grocery Store", "Coffee Shop", "Gas Station",
                        "Restaurant", "Online Shopping", "Utility Bill",
                    ]),
                    date=current,
                    category_hint=random.choice([
                        "Food & Dining", "Transportation", "Shopping", "Utilities"
                    ]),
                ))
            current += timedelta(days=1)
        return txns
