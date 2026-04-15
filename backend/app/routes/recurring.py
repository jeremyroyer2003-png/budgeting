from datetime import date
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import RecurringTransaction, Account

recurring_bp = Blueprint("recurring", __name__)

DEFAULT_USER_ID = 1


def _user_account_ids():
    return [a.id for a in Account.query.filter_by(user_id=DEFAULT_USER_ID).all()]


@recurring_bp.get("/")
def list_recurring():
    account_ids = _user_account_ids()
    rules = RecurringTransaction.query.filter(
        RecurringTransaction.account_id.in_(account_ids),
        RecurringTransaction.is_active == True,
    ).all()
    return jsonify([r.to_dict() for r in rules])


@recurring_bp.post("/")
def create_recurring():
    data = request.get_json()
    if not data or not data.get("amount") or not data.get("type"):
        return jsonify({"error": "amount and type are required"}), 400

    account_ids = _user_account_ids()
    account_id = data.get("account_id")
    if account_id not in account_ids:
        return jsonify({"error": "Account not found"}), 404

    start = date.fromisoformat(data["start_date"]) if data.get("start_date") else date.today()
    rule = RecurringTransaction(
        account_id=account_id,
        category_id=data.get("category_id"),
        amount=float(data["amount"]),
        type=data["type"],
        description=data.get("description", ""),
        frequency=data.get("frequency", "monthly"),
        start_date=start,
        next_date=start,
        end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(rule.to_dict()), 201


@recurring_bp.put("/<int:rule_id>")
def update_recurring(rule_id):
    account_ids = _user_account_ids()
    rule = RecurringTransaction.query.filter(
        RecurringTransaction.id == rule_id,
        RecurringTransaction.account_id.in_(account_ids),
    ).first_or_404()

    data = request.get_json()
    for field in ("description", "frequency", "category_id"):
        if field in data:
            setattr(rule, field, data[field])
    if "amount" in data:
        rule.amount = float(data["amount"])
    if "is_active" in data:
        rule.is_active = bool(data["is_active"])
    if "end_date" in data:
        rule.end_date = date.fromisoformat(data["end_date"]) if data["end_date"] else None

    db.session.commit()
    return jsonify(rule.to_dict())


@recurring_bp.delete("/<int:rule_id>")
def delete_recurring(rule_id):
    account_ids = _user_account_ids()
    rule = RecurringTransaction.query.filter(
        RecurringTransaction.id == rule_id,
        RecurringTransaction.account_id.in_(account_ids),
    ).first_or_404()
    rule.is_active = False
    db.session.commit()
    return jsonify({"deleted": rule_id})
