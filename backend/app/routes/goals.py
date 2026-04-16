from datetime import date
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Goal
from ..services.goal_service import enrich_goal

goals_bp = Blueprint("goals", __name__)

DEFAULT_USER_ID = 1


@goals_bp.get("/")
def list_goals():
    goals = Goal.query.filter_by(user_id=DEFAULT_USER_ID, is_active=True).all()
    return jsonify([enrich_goal(g) for g in goals])


VALID_GOAL_TYPES = {"savings", "investment", "debt_payoff", "purchase"}


@goals_bp.post("/")
def create_goal():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    errors = {}
    if not data.get("name", "").strip():
        errors["name"] = "Required."

    raw_target = data.get("target_amount")
    parsed_target = None
    if raw_target is None:
        errors["target_amount"] = "Required."
    else:
        try:
            parsed_target = float(raw_target)
            if parsed_target <= 0:
                errors["target_amount"] = "Must be greater than 0."
        except (TypeError, ValueError):
            errors["target_amount"] = "Must be a valid number."

    goal_type = data.get("type", "savings")
    if goal_type not in VALID_GOAL_TYPES:
        errors["type"] = f"Must be one of: {', '.join(sorted(VALID_GOAL_TYPES))}."

    raw_current = data.get("current_amount", 0.0)
    try:
        parsed_current = float(raw_current)
        if parsed_current < 0:
            errors["current_amount"] = "Cannot be negative."
    except (TypeError, ValueError):
        errors["current_amount"] = "Must be a valid number."
        parsed_current = 0.0

    parsed_monthly = None
    if data.get("monthly_target") is not None:
        try:
            parsed_monthly = float(data["monthly_target"])
            if parsed_monthly < 0:
                errors["monthly_target"] = "Cannot be negative."
        except (TypeError, ValueError):
            errors["monthly_target"] = "Must be a valid number."

    parsed_date = None
    if data.get("target_date"):
        try:
            parsed_date = date.fromisoformat(data["target_date"])
        except (ValueError, TypeError):
            errors["target_date"] = "Must be a valid date in YYYY-MM-DD format."

    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    goal = Goal(
        user_id=DEFAULT_USER_ID,
        name=data["name"].strip(),
        type=goal_type,
        target_amount=parsed_target,
        current_amount=parsed_current,
        monthly_target=parsed_monthly,
        target_date=parsed_date,
        notes=data.get("notes"),
    )
    db.session.add(goal)
    db.session.commit()
    return jsonify(enrich_goal(goal)), 201


@goals_bp.put("/<int:goal_id>")
def update_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=DEFAULT_USER_ID).first_or_404()
    data = request.get_json()

    for field in ("name", "type", "notes"):
        if field in data:
            setattr(goal, field, data[field])
    for amount_field in ("target_amount", "current_amount", "monthly_target"):
        if amount_field in data and data[amount_field] is not None:
            setattr(goal, amount_field, float(data[amount_field]))
    if "target_date" in data:
        if data["target_date"]:
            try:
                goal.target_date = date.fromisoformat(data["target_date"])
            except (ValueError, TypeError):
                return jsonify({"error": "Validation failed", "fields": {"target_date": "Must be a valid date in YYYY-MM-DD format."}}), 400
        else:
            goal.target_date = None
    if "is_active" in data:
        goal.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(enrich_goal(goal))


@goals_bp.delete("/<int:goal_id>")
def delete_goal(goal_id):
    goal = Goal.query.filter_by(id=goal_id, user_id=DEFAULT_USER_ID).first_or_404()
    goal.is_active = False  # soft delete
    db.session.commit()
    return jsonify({"deleted": goal_id})
