"""
health_score_service.py — Computes a 0-100 financial health score.

Four equal components (25 pts each):
  1. Savings Rate     — 3-month rolling average; full marks at ≥20%
  2. Budget Adherence — fraction of budget lines on or under limit
  3. Goal Progress    — actual vs expected pace (ghost_pct) per goal
  4. Spending Trend   — current month's daily rate vs previous month

Each component returns a detail (what's happening) and a tip (what to do).
"""

import calendar
from ..extensions import db
from sqlalchemy import extract, func


def compute_health_score(uid: int, month: int, year: int) -> dict:
    from ..models.account import Account
    account_ids = [a.id for a in Account.query.filter_by(user_id=uid).all()]
    if not account_ids:
        return _no_data()

    sr_pts, sr_detail, sr_tip = _savings_rate(account_ids, month, year)
    ba_pts, ba_detail, ba_tip = _budget_adherence(uid, month, year)
    gp_pts, gp_detail, gp_tip = _goal_progress(uid)
    st_pts, st_detail, st_tip = _spending_trend(account_ids, month, year)

    total = max(0, min(100, round(sr_pts + ba_pts + gp_pts + st_pts)))

    if total >= 85:
        label, color = "Excellent", "#059669"
    elif total >= 70:
        label, color = "Good",      "#16a34a"
    elif total >= 50:
        label, color = "Fair",      "#d97706"
    else:
        label, color = "Needs Work", "#dc2626"

    return {
        "score": total,
        "label": label,
        "color": color,
        "components": {
            "savings_rate":     {"score": round(sr_pts), "max": 25, "detail": sr_detail, "tip": sr_tip},
            "budget_adherence": {"score": round(ba_pts), "max": 25, "detail": ba_detail, "tip": ba_tip},
            "goal_progress":    {"score": round(gp_pts), "max": 25, "detail": gp_detail, "tip": gp_tip},
            "spending_trend":   {"score": round(st_pts), "max": 25, "detail": st_detail, "tip": st_tip},
        },
    }


# ── Component calculators ─────────────────────────────────────────────────────

def _savings_rate(account_ids, month, year):
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
        return 12.5, "No income data", "Add your income transactions to unlock this score."

    avg = sum(rates) / len(rates)
    pts = min(1.0, max(0.0, avg / 20.0)) * 25

    if avg >= 20:
        tip = f"You're saving {avg:.1f}% — above the 20% target. Keep it up!"
    elif avg > 0:
        gap = round(20.0 - avg, 1)
        tip = f"Saving {gap:.1f}% more of your income would reach the 20% target and max this score."
    else:
        tip = "Your expenses are exceeding your income. Reducing one recurring cost could shift this quickly."

    return pts, f"{avg:.1f}% avg savings rate (3-month)", tip


def _budget_adherence(uid, month, year):
    from ..services.budget_service import get_budget_summary
    summary = get_budget_summary(uid, month, year)
    if not summary:
        return 12.5, "No budgets set", "Set budgets for your top 3 spending categories to unlock this score."

    scores = []
    worst = None
    worst_over = 0
    for b in summary:
        pct = b["pct_used"]
        s = 1.0 if pct <= 100 else max(0.0, 1.0 - (pct - 100) / 100.0)
        scores.append(s)
        over = b["actual_amount"] - b["target_amount"]
        if b["over_budget"] and over > worst_over:
            worst_over = over
            worst = b

    avg = sum(scores) / len(scores)
    on_track = sum(1 for b in summary if not b["over_budget"])

    if worst:
        tip = (
            f"Your biggest overspend is {worst['category_name']} "
            f"(${worst_over:,.2f} over). Pulling this one back would add the most points."
        )
    elif on_track == len(summary):
        tip = "All budgets on track — review them monthly to make sure they still fit your life."
    else:
        tip = "Stay within your remaining budgets for the rest of the month to improve this score."

    return avg * 25, f"{on_track}/{len(summary)} budgets on track", tip


def _goal_progress(uid):
    from ..models.goal import Goal
    from ..services.goal_service import enrich_goal
    goals = Goal.query.filter_by(user_id=uid, is_active=True).all()
    if not goals:
        return 12.5, "No active goals", "Add a savings goal to start tracking your progress toward what matters most."

    scores, on_track = [], 0
    most_behind = None
    biggest_gap = 0

    for g in goals:
        e = enrich_goal(g)
        ghost    = e.get("ghost_pct") or 0
        progress = e.get("progress_pct") or 0

        if progress >= 100:
            s = 1.0
        elif ghost <= 0:
            s = 0.75
        else:
            s = min(1.0, progress / ghost)

        scores.append(s)
        if progress >= ghost or progress >= 100:
            on_track += 1
        else:
            gap = ghost - progress
            if gap > biggest_gap:
                biggest_gap = gap
                most_behind = (g, e)

    avg = sum(scores) / len(scores)

    if most_behind:
        g, e = most_behind
        needed = e.get("needed_per_month")
        monthly = g.monthly_target or 0
        if needed and needed > monthly:
            short = round(needed - monthly, 2)
            tip = (
                f"'{g.name}' is most behind pace. "
                f"Adding ${short:,.2f}/month would bring it back on track."
            )
        else:
            tip = f"'{g.name}' is behind schedule. Any extra contribution this month helps."
    elif on_track == len(goals):
        tip = "All goals on pace — great discipline! Consider raising a target to stay challenged."
    else:
        tip = "Keep contributing consistently. Even small amounts compound into big results."

    return avg * 25, f"{on_track}/{len(goals)} goals on pace", tip


def _spending_trend(account_ids, month, year):
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
        return 12.5, "Insufficient data", "Add more transactions over a few months to unlock trend tracking."

    ratio = prev_daily / curr_daily
    pts   = max(0.0, min(25.0, (ratio - 0.7) / 0.4 * 25))
    pct   = (curr_daily - prev_daily) / prev_daily * 100

    if pct < -5:
        detail = f"Spending down {abs(pct):.0f}% vs last month"
        tip    = f"You're spending ${round((prev_daily - curr_daily) * 30, 2):,.2f} less per month than last month — keep that momentum."
    elif pct > 5:
        diff = round((curr_daily - prev_daily) * 30, 2)
        detail = f"Spending up {pct:.0f}% vs last month"
        tip    = f"Your spending is ${diff:,.2f}/month higher than last month. Identifying one category to cut could flip this trend."
    else:
        detail = "Spending stable vs last month"
        tip    = "Spending is steady. Now's a good time to push savings a little higher."

    return pts, detail, tip


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
    neutral = {"score": 0, "max": 25, "detail": "No accounts", "tip": "Connect an account to get started."}
    return {
        "score": 0, "label": "No Data", "color": "#9ca3af",
        "components": {k: dict(neutral) for k in
                       ("savings_rate", "budget_adherence", "goal_progress", "spending_trend")},
    }
