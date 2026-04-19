"""
weekly_summary_service.py — Computes a rich weekly spending digest.

'This week' = the most recently completed Mon–Sun period.
"""

from datetime import date, timedelta
from sqlalchemy import func
from ..extensions import db


def get_week_bounds(today=None):
    """Return (week_start, week_end) for the most recently completed Mon–Sun."""
    if today is None:
        today = date.today()
    # weekday(): Mon=0 … Sun=6
    # If today is Mon (0) we go back 7 days; otherwise back to last Monday
    days_back = today.weekday() or 7   # 0 → 7, so Mon always gives previous week
    week_start = today - timedelta(days=days_back)
    week_end   = week_start + timedelta(days=6)
    return week_start, week_end


def compute_weekly_summary(account_ids: list) -> dict | None:
    from ..models.transaction import Transaction
    from ..models.category  import Category

    if not account_ids:
        return None

    today = date.today()
    ws, we = get_week_bounds(today)
    ps, pe = ws - timedelta(days=7), we - timedelta(days=7)

    this_inc = _period_total(account_ids, "income",  ws, we)
    this_exp = _period_total(account_ids, "expense", ws, we)
    prev_exp = _period_total(account_ids, "expense", ps, pe)

    tx_count = db.session.query(func.count(Transaction.id)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.date >= ws,
        Transaction.date <= we,
    ).scalar() or 0

    # Week-over-week expense change
    if prev_exp > 0:
        wow_pct = round((this_exp - prev_exp) / prev_exp * 100, 1)
    else:
        wow_pct = None

    # Top spending categories this week
    rows = (
        db.session.query(
            Category.name, Category.color,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == "expense",
            Transaction.date >= ws,
            Transaction.date <= we,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(5)
        .all()
    )
    top_cats = [{"name": r.name, "color": r.color, "total": round(r.total, 2)} for r in rows]

    # Daily breakdown Mon–Sun
    daily = []
    for i in range(7):
        d = ws + timedelta(days=i)
        exp = _period_total(account_ids, "expense", d, d)
        daily.append({"date": d.isoformat(), "label": d.strftime("%a"), "amount": exp})

    challenge = _compute_challenge(top_cats, wow_pct, this_exp, prev_exp)

    return {
        "week_start":  ws.isoformat(),
        "week_end":    we.isoformat(),
        "week_label":  f"{ws.strftime('%b %d')} – {we.strftime('%b %d, %Y')}",
        "total_income":  round(this_inc, 2),
        "total_expense": round(this_exp, 2),
        "net":           round(this_inc - this_exp, 2),
        "prev_expense":  round(prev_exp, 2),
        "wow_pct":       wow_pct,
        "tx_count":      tx_count,
        "top_categories": top_cats,
        "daily":          daily,
        "challenge":      challenge,
    }


def _compute_challenge(top_cats, wow_pct, this_exp, prev_exp) -> str:
    """Return one concrete, achievable challenge for the coming week."""
    if not top_cats:
        return "Log every expense this week — awareness is the first step to change."

    top = top_cats[0]
    if wow_pct is not None and wow_pct > 10:
        target = round(top["total"] * 0.9, 2)
        return (
            f"Your spending jumped {wow_pct:.0f}% vs last week. "
            f"This week, try to keep {top['name']} under ${target:,.2f} — "
            f"that's 10% less than what you spent on it last week."
        )
    elif wow_pct is not None and wow_pct < -10:
        return (
            f"You spent {abs(wow_pct):.0f}% less than last week — great discipline! "
            f"This week, redirect those savings to your top financial goal."
        )
    elif this_exp > 0:
        target = round(this_exp * 0.95, 2)
        return (
            f"Your biggest spend was {top['name']} at ${top['total']:,.2f}. "
            f"This week, see if you can reduce it by just 5% — "
            f"small cuts add up to ${round(top['total'] * 0.05 * 52, 0):,.0f}/year."
        )
    return "Track every purchase this week, no matter how small. Awareness changes behaviour."


def weekly_alert_message(summary: dict) -> str:
    wow = ""
    if summary["wow_pct"] is not None:
        arrow = "↑" if summary["wow_pct"] > 0 else "↓"
        wow = f" ({arrow}{abs(summary['wow_pct']):.0f}% vs prior week)"
    return (
        f"Week of {summary['week_label']}: "
        f"${summary['total_expense']:,.2f} spent{wow}. "
        f"{summary['tx_count']} transaction{'s' if summary['tx_count'] != 1 else ''}."
    )[:500]


# ── Helper ────────────────────────────────────────────────────────────────────

def _period_total(account_ids, tx_type, start, end):
    from ..models.transaction import Transaction
    result = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.type == tx_type,
        Transaction.date >= start,
        Transaction.date <= end,
    ).scalar()
    return float(result or 0.0)
