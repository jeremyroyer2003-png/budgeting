from datetime import date
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Budget, Category
from ..services.budget_service import get_budget_summary

budgets_bp = Blueprint("budgets", __name__)

DEFAULT_USER_ID = 1


@budgets_bp.get("/")
def list_budgets():
    month = request.args.get("month", type=int, default=date.today().month)
    year = request.args.get("year", type=int, default=date.today().year)
    budgets = Budget.query.filter_by(user_id=DEFAULT_USER_ID, month=month, year=year).all()
    return jsonify([b.to_dict() for b in budgets])


@budgets_bp.post("/")
def create_or_update_budget():
    data = request.get_json()
    if not data or not data.get("category_id") or not data.get("target_amount"):
        return jsonify({"error": "category_id and target_amount are required"}), 400

    month = data.get("month", date.today().month)
    year = data.get("year", date.today().year)

    # Upsert: update if exists
    budget = Budget.query.filter_by(
        user_id=DEFAULT_USER_ID,
        category_id=data["category_id"],
        month=month,
        year=year,
    ).first()

    if budget:
        budget.target_amount = float(data["target_amount"])
    else:
        budget = Budget(
            user_id=DEFAULT_USER_ID,
            category_id=data["category_id"],
            month=month,
            year=year,
            target_amount=float(data["target_amount"]),
        )
        db.session.add(budget)

    db.session.commit()
    return jsonify(budget.to_dict()), 201


@budgets_bp.delete("/<int:budget_id>")
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=DEFAULT_USER_ID).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"deleted": budget_id})


@budgets_bp.get("/summary")
def budget_summary():
    month = request.args.get("month", type=int, default=date.today().month)
    year = request.args.get("year", type=int, default=date.today().year)
    summary = get_budget_summary(DEFAULT_USER_ID, month, year)
    return jsonify(summary)
