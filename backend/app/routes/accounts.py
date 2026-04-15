from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Account

accounts_bp = Blueprint("accounts", __name__)

DEFAULT_USER_ID = 1


@accounts_bp.get("/")
def list_accounts():
    accounts = Account.query.filter_by(user_id=DEFAULT_USER_ID).all()
    return jsonify([a.to_dict() for a in accounts])


@accounts_bp.post("/")
def create_account():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400

    account = Account(
        user_id=DEFAULT_USER_ID,
        name=data["name"],
        type=data.get("type", "checking"),
        balance=float(data.get("balance", 0.0)),
        institution=data.get("institution"),
        account_number_last4=data.get("account_number_last4"),
    )
    db.session.add(account)
    db.session.commit()
    return jsonify(account.to_dict()), 201


@accounts_bp.put("/<int:account_id>")
def update_account(account_id):
    account = Account.query.filter_by(id=account_id, user_id=DEFAULT_USER_ID).first_or_404()
    data = request.get_json()
    for field in ("name", "type", "institution", "account_number_last4"):
        if field in data:
            setattr(account, field, data[field])
    if "balance" in data:
        account.balance = float(data["balance"])
    db.session.commit()
    return jsonify(account.to_dict())


@accounts_bp.delete("/<int:account_id>")
def delete_account(account_id):
    account = Account.query.filter_by(id=account_id, user_id=DEFAULT_USER_ID).first_or_404()
    db.session.delete(account)
    db.session.commit()
    return jsonify({"deleted": account_id})
