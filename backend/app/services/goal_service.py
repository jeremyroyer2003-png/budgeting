from datetime import date


def enrich_goal(goal) -> dict:
    """
    Adds on-track status and projected completion date to a goal dict.
    """
    data = goal.to_dict()

    remaining = max(goal.target_amount - goal.current_amount, 0.0)
    data["remaining"] = round(remaining, 2)

    # Determine on-track status
    if goal.target_date and goal.monthly_target:
        today = date.today()
        months_left = _months_between(today, goal.target_date)
        needed_per_month = remaining / months_left if months_left > 0 else remaining
        data["months_left"] = max(int(months_left), 0)
        data["needed_per_month"] = round(needed_per_month, 2)
        data["on_track"] = goal.monthly_target >= needed_per_month
    elif goal.monthly_target and goal.monthly_target > 0:
        months_to_complete = remaining / goal.monthly_target
        data["months_to_complete"] = round(months_to_complete, 1)
        data["on_track"] = True  # no deadline, just tracking progress
    else:
        data["on_track"] = None
        data["months_left"] = None
        data["needed_per_month"] = None

    return data


def _months_between(start: date, end: date) -> float:
    """Approximate number of months between two dates."""
    return (end.year - start.year) * 12 + (end.month - start.month) + (end.day - start.day) / 30.0
