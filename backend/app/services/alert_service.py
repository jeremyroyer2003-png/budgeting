import calendar
from datetime import date
from ..extensions import db
from ..models import Alert, Goal
from .budget_service import get_budget_summary
from .goal_service import enrich_goal, _months_between


def generate_alerts(user_id: int) -> int:
    """
    Evaluate current budget and goal state, auto-resolve stale alerts,
    and create new alerts for active conditions.
    Returns the number of new alerts created.
    """
    today = date.today()
    month, year = today.month, today.year
    days_in_month  = calendar.monthrange(year, month)[1]
    days_remaining = days_in_month - today.day
    created = 0

    # ── Budget alerts ───────────────────────────────────────────────────────
    budget_items = get_budget_summary(user_id, month, year)

    active_over_ids    = {i["category_id"] for i in budget_items if i["over_budget"]}
    active_warning_ids = {i["category_id"] for i in budget_items if i["pct_used"] >= 80 and not i["over_budget"]}
    active_alert_ids   = active_over_ids | active_warning_ids

    # Auto-dismiss alerts for categories back under budget
    stale = Alert.query.filter_by(user_id=user_id, type="overspending", is_read=False).all()
    for alert in stale:
        if alert.category_id not in active_alert_ids:
            alert.is_read = True

    for item in budget_items:
        cat   = item["category_name"]
        over  = round(item["actual_amount"] - item["target_amount"], 2)
        left  = round(item["target_amount"]  - item["actual_amount"], 2)

        if item["over_budget"]:
            if days_remaining > 1:
                recover_daily = round(over / days_remaining, 2)
                msg = (
                    f"You're ${over:,.2f} over your {cat} budget with "
                    f"{days_remaining} days left this month. "
                    f"Spending ${recover_daily:,.2f}/day less on {cat} "
                    f"would close the gap before month-end."
                )
            else:
                msg = (
                    f"You finished the month ${over:,.2f} over your {cat} budget "
                    f"({item['pct_used']:.0f}% used). "
                    f"Consider raising the limit or reducing {cat} spending next month."
                )
            if _ensure_alert(user_id, "overspending", "critical", msg[:500], item["category_id"]):
                created += 1

        elif item["pct_used"] >= 80:
            if days_remaining > 0:
                daily_budget = round(left / days_remaining, 2)
                msg = (
                    f"You have ${left:,.2f} left in {cat} for "
                    f"{days_remaining} more day{'s' if days_remaining != 1 else ''} "
                    f"— that's ${daily_budget:,.2f}/day. "
                    f"You're at {item['pct_used']:.0f}% of your budget."
                )
            else:
                msg = (
                    f"You used {item['pct_used']:.0f}% of your {cat} budget this month "
                    f"(${item['actual_amount']:,.2f} of ${item['target_amount']:,.2f})."
                )
            if _ensure_alert(user_id, "overspending", "warning", msg[:500], item["category_id"]):
                created += 1

    # ── Goal alerts ─────────────────────────────────────────────────────────
    goals = Goal.query.filter_by(user_id=user_id, is_active=True).all()
    for goal in goals:
        enriched = enrich_goal(goal)

        if enriched.get("on_track") is False:
            gap = round(enriched["needed_per_month"] - (goal.monthly_target or 0), 2)
            months_left = enriched.get("months_left") or 0
            msg = (
                f"'{goal.name}' needs ${enriched['needed_per_month']:,.2f}/month to reach "
                f"${goal.target_amount:,.2f} by your target date, but you've set aside "
                f"${goal.monthly_target:,.2f}/month — ${gap:,.2f} short. "
                f"Increasing your monthly contribution would move the goal date "
                f"{'closer' if months_left > 0 else 'back on track'}."
            )
            if _ensure_alert(user_id, "goal_at_risk", "warning", msg[:500], None):
                created += 1

        if goal.type in ("savings", "investment") and not goal.monthly_target:
            suggestion = round(goal.target_amount / 24, 2)
            msg = (
                f"'{goal.name}' has no monthly savings target yet. "
                f"Setting even ${suggestion:,.2f}/month would get you there in 2 years — "
                f"add a target to start tracking your progress."
            )
            if _ensure_alert(user_id, "savings_behind", "info", msg[:500], None):
                created += 1

    db.session.commit()
    return created


def _ensure_alert(user_id, alert_type, severity, message, category_id) -> bool:
    exists = Alert.query.filter_by(
        user_id=user_id,
        type=alert_type,
        category_id=category_id,
        is_read=False,
    ).first()
    if not exists:
        db.session.add(Alert(
            user_id=user_id,
            type=alert_type,
            severity=severity,
            message=message,
            category_id=category_id,
        ))
        return True
    return False
