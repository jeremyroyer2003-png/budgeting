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
    created = 0

    # ── Budget overspending alerts ──────────────────────────────────────────
    budget_items = get_budget_summary(user_id, month, year)

    # Category IDs that are currently triggering an overspend condition
    active_over_ids   = {i["category_id"] for i in budget_items if i["over_budget"]}
    active_warning_ids = {i["category_id"] for i in budget_items if i["pct_used"] >= 80 and not i["over_budget"]}
    active_alert_ids  = active_over_ids | active_warning_ids

    # Auto-dismiss overspending alerts for categories now back under budget
    stale = Alert.query.filter_by(
        user_id=user_id,
        type="overspending",
        is_read=False,
    ).all()
    for alert in stale:
        if alert.category_id not in active_alert_ids:
            alert.is_read = True   # silently resolve — no longer relevant

    for item in budget_items:
        if item["over_budget"]:
            if _ensure_alert(
                user_id=user_id,
                alert_type="overspending",
                severity="critical",
                message=(
                    f"You've exceeded your {item['category_name']} budget: "
                    f"spent ${item['actual_amount']:,.2f} of "
                    f"${item['target_amount']:,.2f} ({item['pct_used']:.0f}%)."
                ),
                category_id=item["category_id"],
            ):
                created += 1
        elif item["pct_used"] >= 80:
            if _ensure_alert(
                user_id=user_id,
                alert_type="overspending",
                severity="warning",
                message=(
                    f"You're at {item['pct_used']:.0f}% of your {item['category_name']} budget "
                    f"(${item['actual_amount']:,.2f} of ${item['target_amount']:,.2f})."
                ),
                category_id=item["category_id"],
            ):
                created += 1

    # ── Goal risk alerts ────────────────────────────────────────────────────
    goals = Goal.query.filter_by(user_id=user_id, is_active=True).all()
    for goal in goals:
        enriched = enrich_goal(goal)
        if enriched.get("on_track") is False:
            if _ensure_alert(
                user_id=user_id,
                alert_type="goal_at_risk",
                severity="warning",
                message=(
                    f"Goal '{goal.name}' is off track. You need "
                    f"${enriched['needed_per_month']:,.2f}/month but have only set aside "
                    f"${goal.monthly_target:,.2f}/month."
                ),
                category_id=None,
            ):
                created += 1

        # Savings behind — goal has no monthly contribution set
        if goal.type in ("savings", "investment") and not goal.monthly_target:
            if _ensure_alert(
                user_id=user_id,
                alert_type="savings_behind",
                severity="info",
                message=(
                    f"Goal '{goal.name}' has no monthly target set. "
                    f"Add a monthly target to track your progress."
                ),
                category_id=None,
            ):
                created += 1

    db.session.commit()
    return created


def _ensure_alert(user_id, alert_type, severity, message, category_id) -> bool:
    """
    Create an alert only if an identical unread one doesn't already exist.
    Returns True if a new alert was created, False if it already existed.
    """
    exists = Alert.query.filter_by(
        user_id=user_id,
        type=alert_type,
        category_id=category_id,
        is_read=False,
    ).first()
    if not exists:
        alert = Alert(
            user_id=user_id,
            type=alert_type,
            severity=severity,
            message=message,
            category_id=category_id,
        )
        db.session.add(alert)
        return True
    return False
