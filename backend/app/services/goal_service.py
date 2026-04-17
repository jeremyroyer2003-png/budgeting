from datetime import date, timedelta


def enrich_goal(goal) -> dict:
    """Adds on-track status, velocity, and ghost-bar data to a goal dict."""
    data = goal.to_dict()

    remaining = max(goal.target_amount - goal.current_amount, 0.0)
    data["remaining"] = round(remaining, 2)

    # ── Static on-track (monthly_target vs needed pace) ──────────────────────
    if goal.target_date and goal.monthly_target:
        today = date.today()
        months_left = _months_between(today, goal.target_date)
        needed_per_month = remaining / months_left if months_left > 0 else remaining
        data["months_left"]      = max(int(months_left), 0)
        data["needed_per_month"] = round(needed_per_month, 2)
        data["on_track"]         = goal.monthly_target >= needed_per_month
    elif goal.monthly_target and goal.monthly_target > 0:
        months_to_complete       = remaining / goal.monthly_target
        data["months_to_complete"] = round(months_to_complete, 1)
        data["on_track"]         = True
    else:
        data["on_track"]         = None
        data["months_left"]      = None
        data["needed_per_month"] = None

    # ── Velocity engine ───────────────────────────────────────────────────────
    data.update(calculate_goal_velocity(goal))

    return data


def calculate_goal_velocity(goal) -> dict:
    """
    Analyses the user's last-30-day transactions to compute real savings pace
    and project when this goal will be reached.

    Returns a dict with:
      velocity_30d          — net savings over last 30 days
      daily_pace            — velocity_30d / 30
      projected_completion  — ISO date string (or None)
      projected_months_diff — positive = behind schedule, negative = ahead
      ghost_pct             — planned % complete today (linear from creation→target)
    """
    # Lazy import to avoid circular deps at module load time
    from ..models.transaction import Transaction
    from ..models.account import Account

    today  = date.today()
    cutoff = today - timedelta(days=30)

    account_ids = [
        a.id for a in Account.query.filter_by(user_id=goal.user_id).all()
    ]
    if not account_ids:
        return _empty_velocity()

    recent = Transaction.query.filter(
        Transaction.account_id.in_(account_ids),
        Transaction.date >= cutoff,
    ).all()

    income_30d  = sum(t.amount for t in recent if t.type == "income")
    expense_30d = sum(t.amount for t in recent if t.type == "expense")
    net_30d     = income_30d - expense_30d          # true net savings
    daily_pace  = net_30d / 30.0

    remaining = max(goal.target_amount - goal.current_amount, 0.0)

    projected_completion  = None
    projected_months_diff = None

    if remaining <= 0:
        projected_completion  = today
        projected_months_diff = 0.0
    elif daily_pace > 0:
        days_needed          = remaining / daily_pace
        projected_completion = today + timedelta(days=days_needed)
        if goal.target_date:
            # positive  → projected date is AFTER target  → behind schedule
            # negative  → projected date is BEFORE target → ahead of schedule
            projected_months_diff = round(
                _months_between(goal.target_date, projected_completion), 1
            )

    # ── Ghost bar ─────────────────────────────────────────────────────────────
    # Shows "where you should be today" assuming linear progress from creation.
    ghost_pct = None
    if goal.target_date and goal.created_at:
        total_days   = max((goal.target_date - goal.created_at.date()).days, 1)
        days_elapsed = (today - goal.created_at.date()).days
        ghost_pct    = round(min(max(days_elapsed / total_days * 100, 0), 100), 1)

    return {
        "velocity_30d":          round(net_30d, 2),
        "daily_pace":            round(daily_pace, 2),
        "projected_completion":  projected_completion.isoformat() if projected_completion else None,
        "projected_months_diff": projected_months_diff,
        "ghost_pct":             ghost_pct,
    }


def _empty_velocity() -> dict:
    return {
        "velocity_30d": 0.0,
        "daily_pace": 0.0,
        "projected_completion": None,
        "projected_months_diff": None,
        "ghost_pct": None,
    }


def _months_between(start: date, end: date) -> float:
    """Signed month difference: positive when end is after start."""
    return (
        (end.year - start.year) * 12
        + (end.month - start.month)
        + (end.day - start.day) / 30.0
    )
