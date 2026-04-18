"""
transfer_detection_service.py — Detects internal transfers between accounts.

Two detection layers:

  Layer 1 — Keyword scan (immediate, O(1))
    Marks a transaction as a transfer based on its description alone.
    Runs synchronously when a transaction is created or imported.

  Layer 2 — Amount/timing match (72-hour window)
    Finds a paired transaction in another account with the same amount,
    opposite type (one income / one expense), within 3 days.
    Runs after a flush so both sides are in the DB.

Transfers are excluded from budget and dashboard calculations but remain
visible in the transaction list with a "Transfer" badge.
"""

from datetime import timedelta

from sqlalchemy import func

from ..models.transaction import Transaction


# ── Layer 1: keyword list (EN + FR) ───────────────────────────────────────────

_TRANSFER_KEYWORDS = [
    # English
    "transfer", "xfer",
    "from savings", "to savings",
    "from chequing", "to chequing",
    "from checking", "to checking",
    "from account", "to account",
    "e-transfer", "etransfer", "interac",
    "credit card payment", "card payment", "visa payment",
    "mastercard payment", "line of credit payment",
    "loan payment", "mortgage payment",
    "move money", "sweep",
    # French
    "virement", "transfert",
    "de épargne", "vers épargne",
    "de chèques", "vers chèques",
    "paiement carte", "paiement visa",
    "paiement mastercard", "remboursement carte",
    "paiement de prêt", "paiement hypothèque",
    "déplacement de fonds",
]


def is_transfer_by_keyword(description: str) -> bool:
    """
    Layer 1: return True if the description contains a known transfer keyword.
    Case-insensitive.
    """
    if not description:
        return False
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in _TRANSFER_KEYWORDS)


# ── Layer 2: amount + timing match ────────────────────────────────────────────

_MATCH_WINDOW_DAYS = 3
_AMOUNT_TOLERANCE  = 0.01   # allow 1-cent rounding difference


def find_transfer_pair(tx: Transaction, user_account_ids: list[int]) -> Transaction | None:
    """
    Layer 2: search for a matching transaction in another account.

    A valid pair satisfies ALL of:
      - Same user (account in user_account_ids)
      - Different account than tx
      - Opposite type (income ↔ expense)
      - Amount within _AMOUNT_TOLERANCE
      - Date within _MATCH_WINDOW_DAYS
      - Not already paired
    """
    other_accounts = [aid for aid in user_account_ids if aid != tx.account_id]
    if not other_accounts:
        return None

    opposite_type = "income" if tx.type == "expense" else "expense"
    window_start  = tx.date - timedelta(days=_MATCH_WINDOW_DAYS)
    window_end    = tx.date + timedelta(days=_MATCH_WINDOW_DAYS)

    candidate = (
        Transaction.query
        .filter(
            Transaction.account_id.in_(other_accounts),
            Transaction.type == opposite_type,
            Transaction.is_transfer == False,           # not already marked
            Transaction.transfer_pair_id == None,       # not already paired
            Transaction.date >= window_start,
            Transaction.date <= window_end,
            func.abs(Transaction.amount - tx.amount) <= _AMOUNT_TOLERANCE,
        )
        .order_by(
            func.abs(Transaction.amount - tx.amount),   # closest amount first
            func.abs(Transaction.date - tx.date),       # then closest date
        )
        .first()
    )
    return candidate


def mark_as_transfer(tx: Transaction, pair: Transaction | None = None) -> None:
    """
    Mark tx (and optionally its pair) as internal transfers.
    Does NOT commit — caller is responsible for db.session.commit().
    """
    tx.is_transfer = True
    if pair:
        pair.is_transfer     = True
        pair.transfer_pair_id = tx.id
        tx.transfer_pair_id  = pair.id


# ── Convenience: run both layers on a single transaction ─────────────────────

def detect_and_mark(tx: Transaction, user_account_ids: list[int]) -> bool:
    """
    Run Layer 1 then Layer 2 on a newly created/imported transaction.

    Returns True if the transaction was marked as a transfer.
    Does NOT commit.
    """
    # Layer 1 — keyword
    if is_transfer_by_keyword(tx.description or ""):
        mark_as_transfer(tx, pair=None)
        return True

    # Layer 2 — amount/timing match
    pair = find_transfer_pair(tx, user_account_ids)
    if pair:
        mark_as_transfer(tx, pair=pair)
        return True

    return False


# ── Bulk scan: run on all existing transactions for a user ────────────────────

def scan_user_transfers(user_account_ids: list[int]) -> dict:
    """
    Run transfer detection on ALL transactions for a user.
    Useful after connecting a new bank account.

    Returns a summary: { "marked": N, "paired": N }
    """
    txns = (
        Transaction.query
        .filter(
            Transaction.account_id.in_(user_account_ids),
            Transaction.is_transfer == False,
        )
        .order_by(Transaction.date.asc(), Transaction.id.asc())
        .all()
    )

    marked = 0
    paired = 0

    for tx in txns:
        if tx.is_transfer:
            continue  # already handled earlier in this loop

        # Layer 1
        if is_transfer_by_keyword(tx.description or ""):
            mark_as_transfer(tx)
            marked += 1
            continue

        # Layer 2
        pair = find_transfer_pair(tx, user_account_ids)
        if pair:
            mark_as_transfer(tx, pair)
            marked += 2
            paired += 1

    return {"marked": marked, "paired": paired}
