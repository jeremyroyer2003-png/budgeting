from sqlalchemy import extract, func
from ..extensions import db
from ..models import Budget, Transaction, Account, Category


def get_actuals(user_id: int, month: int, year: int) -> dict:
    """Return actual spending per category_id for the given month/year."""
    account_ids = [a.id for a in Account.query.filter_by(user_id=user_id).all()]

    rows = (
        db.session.query(Transaction.category_id, func.sum(Transaction.amount).label("total"))
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == "expense",
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
        .group_by(Transaction.category_id)
        .all()
    )
    return {row.category_id: round(row.total, 2) for row in rows}


def get_budget_summary(user_id: int, month: int, year: int) -> list:
    """
    Returns one entry per budget category with:
      - target_amount
      - actual_amount (spent this month)
      - remaining (target - actual)
      - over_budget (bool)
      - pct_used
    """
    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    actuals = get_actuals(user_id, month, year)

    summary = []
    for b in budgets:
        actual = actuals.get(b.category_id, 0.0)
        remaining = round(b.target_amount - actual, 2)
        # pct_used is NOT capped at 100 — callers that want to display a bar should
        # clamp the width themselves, but the raw value must reflect the true overrun
        # (e.g. 143% when $143 is spent against a $100 budget).
        pct_used = round(actual / b.target_amount * 100, 1) if b.target_amount > 0 else 0.0
        summary.append({
            "budget_id": b.id,
            "category_id": b.category_id,
            "category_name": b.category.name if b.category else None,
            "category_color": b.category.color if b.category else None,
            "target_amount": b.target_amount,
            "actual_amount": actual,
            "remaining": remaining,
            "over_budget": actual > b.target_amount,
            "pct_used": pct_used,
            "month": month,
            "year": year,
        })

    return sorted(summary, key=lambda x: x["pct_used"], reverse=True)
