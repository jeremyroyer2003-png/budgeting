from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import RecurringTransaction, Account
from ..utils.auth import current_user_id

recurring_bp = Blueprint("recurring", __name__)

VALID_TX_TYPES    = {"income", "expense"}
VALID_FREQUENCIES = {"daily", "weekly", "monthly", "yearly"}


def _user_account_ids():
    return [a.id for a in Account.query.filter_by(user_id=current_user_id()).all()]


@recurring_bp.get("/")
@jwt_required()
def list_recurring():
    account_ids = _user_account_ids()
    rules = RecurringTransaction.query.filter(
        RecurringTransaction.account_id.in_(account_ids),
        RecurringTransaction.is_active == True,
    ).all()
    return jsonify([r.to_dict() for r in rules])


@recurring_bp.post("/")
@jwt_required()
def create_recurring():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    errors = {}

    tx_type = data.get("type")
    if tx_type not in VALID_TX_TYPES:
        errors["type"] = "Must be 'income' or 'expense'."

    raw_amount = data.get("amount")
    parsed_amount = None
    if raw_amount is None:
        errors["amount"] = "Required."
    else:
        try:
            parsed_amount = float(raw_amount)
            if parsed_amount <= 0:
                errors["amount"] = "Must be greater than 0."
        except (TypeError, ValueError):
            errors["amount"] = "Must be a valid number."

    frequency = data.get("frequency", "monthly")
    if frequency not in VALID_FREQUENCIES:
        errors["frequency"] = f"Must be one of: {', '.join(sorted(VALID_FREQUENCIES))}."

    parsed_start = date.today()
    if data.get("start_date"):
        try:
            parsed_start = date.fromisoformat(data["start_date"])
        except (ValueError, TypeError):
            errors["start_date"] = "Must be a valid date in YYYY-MM-DD format."

    parsed_end = None
    if data.get("end_date"):
        try:
            parsed_end = date.fromisoformat(data["end_date"])
        except (ValueError, TypeError):
            errors["end_date"] = "Must be a valid date in YYYY-MM-DD format."

    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    account_ids = _user_account_ids()
    account_id  = data.get("account_id")
    if account_id not in account_ids:
        return jsonify({"error": "Account not found"}), 404

    rule = RecurringTransaction(
        account_id=account_id,
        category_id=data.get("category_id"),
        amount=parsed_amount,
        type=tx_type,
        description=data.get("description", ""),
        frequency=frequency,
        start_date=parsed_start,
        next_date=parsed_start,
        end_date=parsed_end,
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(rule.to_dict()), 201


@recurring_bp.put("/<int:rule_id>")
@jwt_required()
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
@jwt_required()
def delete_recurring(rule_id):
    account_ids = _user_account_ids()
    rule = RecurringTransaction.query.filter(
        RecurringTransaction.id == rule_id,
        RecurringTransaction.account_id.in_(account_ids),
    ).first_or_404()
    rule.is_active = False
    db.session.commit()
    return jsonify({"deleted": rule_id})
