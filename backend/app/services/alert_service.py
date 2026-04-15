from datetime import date
from ..extensions import db
from ..models import Alert, Goal
from .budget_service import get_budget_summary
from .goal_service import enrich_goal, _months_between


def generate_alerts(user_id: int) -> int:
    """
    Evaluate current budget and goal state and create new alerts.
    Returns the number of new alerts created.

    Existing unread alerts of the same type+category are not duplicated.
    """
    today = date.today()
    month, year = today.month, today.year
    created = 0

    # --- Budget overspending alerts ---
    for item in get_budget_summary(user_id, month, year):
        if item["over_budget"]:
            _ensure_alert(
                user_id=user_id,
                alert_type="overspending",
                severity="critical",
                message=(
                    f"You've exceeded your {item['category_name']} budget: "
                    f"spent ${item['actual_amount']:,.2f} of ${item['target_amount']:,.2f}."
                ),
                category_id=item["category_id"],
                created_counter=lambda: None,
            )
            created += 1
        elif item["pct_used"] >= 80:
            _ensure_alert(
                user_id=user_id,
                alert_type="overspending",
                severity="warning",
                message=(
                    f"You're at {item['pct_used']}% of your {item['category_name']} budget "
                    f"(${item['actual_amount']:,.2f} of ${item['target_amount']:,.2f})."
                ),
                category_id=item["category_id"],
                created_counter=lambda: None,
            )
            created += 1

    # --- Goal risk alerts ---
    goals = Goal.query.filter_by(user_id=user_id, is_active=True).all()
    for goal in goals:
        enriched = enrich_goal(goal)
        if enriched.get("on_track") is False:
            _ensure_alert(
                user_id=user_id,
                alert_type="goal_at_risk",
                severity="warning",
                message=(
                    f"Goal '{goal.name}' is off track. You need "
                    f"${enriched['needed_per_month']:,.2f}/month but have only set aside "
                    f"${goal.monthly_target:,.2f}/month."
                ),
                category_id=None,
                created_counter=lambda: None,
            )
            created += 1

        # Savings behind — goal has no monthly contribution set
        if goal.type in ("savings", "investment") and not goal.monthly_target:
            _ensure_alert(
                user_id=user_id,
                alert_type="savings_behind",
                severity="info",
                message=(
                    f"Goal '{goal.name}' has no monthly target set. "
                    f"Add a monthly target to track your progress."
                ),
                category_id=None,
                created_counter=lambda: None,
            )
            created += 1

    db.session.commit()
    return created


def _ensure_alert(user_id, alert_type, severity, message, category_id, created_counter):
    """Create an alert only if an identical unread one doesn't already exist."""
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
