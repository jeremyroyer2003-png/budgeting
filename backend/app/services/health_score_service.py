"""
health_score_service.py — Computes a 0-100 financial health score.

Four equal components (25 pts each):
  1. Savings Rate     — 3-month rolling average; full marks at ≥20%
  2. Budget Adherence — fraction of budget lines on or under limit
  3. Goal Progress    — actual vs expected pace (ghost_pct) per goal
  4. Spending Trend   — current month's daily rate vs previous month
"""

import calendar
from ..extensions import db
from sqlalchemy import extract, func


def compute_health_score(uid: int, month: int, year: int) -> dict:
    from ..models.account import Account
    account_ids = [a.id for a in Account.query.filter_by(user_id=uid).all()]
    if not account_ids:
        return _no_data()

    sr_pts, sr_detail = _savings_rate(account_ids, month, year)
    ba_pts, ba_detail = _budget_adherence(uid, month, year)
    gp_pts, gp_detail = _goal_progress(uid)
    st_pts, st_detail = _spending_trend(account_ids, month, year)

    total = max(0, min(100, round(sr_pts + ba_pts + gp_pts + st_pts)))

    if total >= 85:
        label, color = "Excellent", "#059669"
    elif total >= 70:
        label, color = "Good",      "#16a34a"
    elif total >= 50:
        label, color = "Fair",      "#d97706"
    else:
        label, color = "Needs Work","#dc2626"

    return {
        "score": total,
        "label": label,
        "color": color,
        "components": {
            "savings_rate":     {"score": round(sr_pts), "max": 25, "detail": sr_detail},
            "budget_adherence": {"score": round(ba_pts), "max": 25, "detail": ba_detail},
            "goal_progress":    {"score": round(gp_pts), "max": 25, "detail": gp_detail},
            "spending_trend":   {"score": round(st_pts), "max": 25, "detail": st_detail},
        },
    }


# ── Component calculators ─────────────────────────────────────────────────────

def _savings_rate(account_ids, month, year):
    """3-month rolling average savings rate; target 20% for full 25 pts."""
    rates = []
    for i in range(3):
        m, y = month - i, year
        while m <= 0:
            m += 12; y -= 1
        inc = _total(account_ids, "income",  m, y)
        exp = _total(account_ids, "expense", m, y)
        if inc > 0:
            rates.append((inc - exp) / inc * 100)

    if not rates:
        return 12.5, "No income data"

    avg = sum(rates) / len(rates)
    pts = min(1.0, max(0.0, avg / 20.0)) * 25
    return pts, f"{avg:.1f}% avg savings rate (3-month)"


def _budget_adherence(uid, month, year):
    from ..services.budget_service import get_budget_summary
    summary = get_budget_summary(uid, month, year)
    if not summary:
        return 12.5, "No budgets set"

    scores = []
    for b in summary:
        pct = b["pct_used"]
        # 0-100% used = full credit; each 1% over costs proportionally up to 100% over
        s = 1.0 if pct <= 100 else max(0.0, 1.0 - (pct - 100) / 100.0)
        scores.append(s)

    avg = sum(scores) / len(scores)
    on_track = sum(1 for b in summary if not b["over_budget"])
    return avg * 25, f"{on_track}/{len(summary)} budgets on track"


def _goal_progress(uid):
    from ..models.goal import Goal
    from ..services.goal_service import enrich_goal
    goals = Goal.query.filter_by(user_id=uid, is_active=True).all()
    if not goals:
        return 12.5, "No active goals"

    scores, on_track = [], 0
    for g in goals:
        e = enrich_goal(g)
        ghost    = e.get("ghost_pct") or 0
        progress = e.get("progress_pct") or 0

        if progress >= 100:
            s = 1.0
        elif ghost <= 0:
            s = 0.75           # no target date set — neutral-ish
        else:
            s = min(1.0, progress / ghost)

        scores.append(s)
        if progress >= ghost or progress >= 100:
            on_track += 1

    avg = sum(scores) / len(scores)
    return avg * 25, f"{on_track}/{len(goals)} goals on pace"


def _spending_trend(account_ids, month, year):
    """Current month daily expense rate vs previous month; lower is better."""
    from datetime import date
    today = date.today()
    is_current = (month == today.month and year == today.year)
    days_elapsed = today.day if is_current else calendar.monthrange(year, month)[1]

    curr_exp   = _total(account_ids, "expense", month, year)
    curr_daily = curr_exp / days_elapsed if days_elapsed else 0

    pm, py = month - 1, year
    if pm <= 0:
        pm += 12; py -= 1
    prev_days  = calendar.monthrange(py, pm)[1]
    prev_exp   = _total(account_ids, "expense", pm, py)
    prev_daily = prev_exp / prev_days if prev_days else 0

    if prev_daily <= 0 or curr_daily <= 0:
        return 12.5, "Insufficient data"

    # ratio > 1 means spending decreased (good); < 1 means increased (bad)
    ratio = prev_daily / curr_daily
    # 1.1 (10% down) → 25 pts; 1.0 (flat) → 15 pts; 0.7 (30% up) → 0 pts
    pts = max(0.0, min(25.0, (ratio - 0.7) / 0.4 * 25))

    pct = (curr_daily - prev_daily) / prev_daily * 100
    if pct < -5:
        detail = f"Spending down {abs(pct):.0f}% vs last month"
    elif pct > 5:
        detail = f"Spending up {pct:.0f}% vs last month"
    else:
        detail = "Spending stable vs last month"

    return pts, detail


# ── Helpers ───────────────────────────────────────────────────────────────────

def _total(account_ids, tx_type, month, year):
    from ..models.transaction import Transaction
    result = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.type == tx_type,
        extract("month", Transaction.date) == month,
        extract("year",  Transaction.date) == year,
    ).scalar()
    return float(result or 0.0)


def _no_data():
    neutral = {"score": 0, "max": 25, "detail": "No accounts"}
    return {
        "score": 0, "label": "No Data", "color": "#9ca3af",
        "components": {k: dict(neutral) for k in
                       ("savings_rate", "budget_adherence", "goal_progress", "spending_trend")},
    }
