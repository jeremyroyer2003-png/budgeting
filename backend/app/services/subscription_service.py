"""
subscription_service.py — Detects recurring subscriptions from transaction history.

Algorithm:
  1. Fetch all expense transactions for the user over the last 13 months
  2. Group by normalized description (lowercase, strip amounts/punctuation)
  3. For groups with 3+ transactions, measure average interval between charges
  4. Classify as: weekly (7d), biweekly (14d), monthly (30d),
                  quarterly (90d), or annual (365d)
  5. Detect price changes (different amounts within same subscription)
  6. Return a list of DetectedSubscription objects

No new DB table needed — computed on demand from existing transactions.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from ..models.transaction import Transaction


# ── Tolerance: ±20% of the expected interval ──────────────────────────────────
_FREQUENCIES = [
    ("weekly",    7),
    ("biweekly", 14),
    ("monthly",  30),
    ("quarterly",90),
    ("annual",  365),
]
_TOLERANCE = 0.20

# Minimum transactions to consider something a subscription
_MIN_OCCURRENCES = 3

# How far back to look
_LOOKBACK_DAYS = 395   # ~13 months


@dataclass
class DetectedSubscription:
    key: str                        # normalized description slug
    name: str                       # display name (cleaned description)
    frequency: str                  # weekly | biweekly | monthly | quarterly | annual
    interval_days: int              # expected days between charges
    monthly_cost: float             # cost normalised to per-month
    last_amount: float              # most recent charge
    last_date: date                 # date of most recent charge
    next_estimated: date            # estimated next charge
    occurrences: int                # how many times detected
    price_changed: bool             # True if amount varied across charges
    price_history: list[float]      # list of distinct amounts seen
    category_name: Optional[str]    # from the category of the last transaction


def detect_subscriptions(user_account_ids: list[int]) -> list[DetectedSubscription]:
    """
    Run subscription detection for a user.
    Returns a list sorted by monthly_cost descending.
    """
    if not user_account_ids:
        return []

    cutoff = date.today() - timedelta(days=_LOOKBACK_DAYS)

    txns = (
        Transaction.query
        .filter(
            Transaction.account_id.in_(user_account_ids),
            Transaction.type == "expense",
            Transaction.is_transfer == False,
            Transaction.date >= cutoff,
        )
        .order_by(Transaction.date.asc())
        .all()
    )

    # Group by normalized key
    groups: dict[str, list[Transaction]] = {}
    for tx in txns:
        key = _normalize(tx.description or "")
        if not key:
            continue
        groups.setdefault(key, []).append(tx)

    results: list[DetectedSubscription] = []

    for key, group in groups.items():
        if len(group) < _MIN_OCCURRENCES:
            continue

        # Sort by date (already sorted but let's be sure)
        group.sort(key=lambda t: t.date)

        # Calculate intervals between consecutive transactions
        intervals = [
            (group[i].date - group[i - 1].date).days
            for i in range(1, len(group))
        ]
        avg_interval = sum(intervals) / len(intervals)

        # Match to a known frequency
        matched_freq = None
        matched_days = None
        for freq_name, expected_days in _FREQUENCIES:
            lo = expected_days * (1 - _TOLERANCE)
            hi = expected_days * (1 + _TOLERANCE)
            if lo <= avg_interval <= hi:
                matched_freq = freq_name
                matched_days = expected_days
                break

        if not matched_freq:
            continue  # irregular — not a subscription

        last_tx      = group[-1]
        amounts      = sorted({round(t.amount, 2) for t in group})
        last_amount  = round(last_tx.amount, 2)
        price_changed = len(amounts) > 1

        monthly_cost = _to_monthly(last_amount, matched_days)

        results.append(DetectedSubscription(
            key             = key,
            name            = _display_name(last_tx.description or key),
            frequency       = matched_freq,
            interval_days   = matched_days,
            monthly_cost    = round(monthly_cost, 2),
            last_amount     = last_amount,
            last_date       = last_tx.date,
            next_estimated  = last_tx.date + timedelta(days=matched_days),
            occurrences     = len(group),
            price_changed   = price_changed,
            price_history   = amounts,
            category_name   = last_tx.category.name if last_tx.category else None,
        ))

    results.sort(key=lambda s: s.monthly_cost, reverse=True)
    return results


def subscription_summary(subs: list[DetectedSubscription]) -> dict:
    """Return total monthly and annual cost across all detected subscriptions."""
    total_monthly = sum(s.monthly_cost for s in subs)
    return {
        "count":          len(subs),
        "total_monthly":  round(total_monthly, 2),
        "total_annual":   round(total_monthly * 12, 2),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

# Words that don't help identify a subscription
_NOISE = re.compile(
    r"\b(payment|paiement|purchase|achat|debit|credit|transaction|"
    r"recurring|automatique|auto|sub|subscription|abonnement|"
    r"inc|ltd|llc|corp|co)\b",
    re.IGNORECASE,
)
_AMOUNTS   = re.compile(r"\$?\d+[\.,]\d{2}")
_NON_ALPHA = re.compile(r"[^a-z0-9 ]")
_SPACES    = re.compile(r"\s+")


def _normalize(description: str) -> str:
    """Reduce a description to a stable key for grouping."""
    s = description.lower()
    s = _AMOUNTS.sub("", s)
    s = _NOISE.sub("", s)
    s = _NON_ALPHA.sub(" ", s)
    s = _SPACES.sub(" ", s).strip()
    return s[:60]  # cap length


def _display_name(description: str) -> str:
    """Capitalise and clean for display."""
    s = _AMOUNTS.sub("", description).strip()
    # Title-case but keep short words lowercase
    return " ".join(w.capitalize() for w in s.split())[:50]


def _to_monthly(amount: float, interval_days: int) -> float:
    """Convert a charge of `amount` every `interval_days` to a monthly equivalent."""
    if interval_days <= 0:
        return 0.0
    return amount * (30.0 / interval_days)
