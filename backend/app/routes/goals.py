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


@goals_bp.post("/")
def create_goal():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("target_amount"):
        return jsonify({"error": "name and target_amount are required"}), 400

    goal = Goal(
        user_id=DEFAULT_USER_ID,
        name=data["name"],
        type=data.get("type", "savings"),
        target_amount=float(data["target_amount"]),
        current_amount=float(data.get("current_amount", 0.0)),
        monthly_target=float(data["monthly_target"]) if data.get("monthly_target") else None,
        target_date=date.fromisoformat(data["target_date"]) if data.get("target_date") else None,
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
        goal.target_date = date.fromisoformat(data["target_date"]) if data["target_date"] else None
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
