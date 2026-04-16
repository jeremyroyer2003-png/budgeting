from datetime import date
from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Transaction, Account, Category

transactions_bp = Blueprint("transactions", __name__)

DEFAULT_USER_ID = 1  # swapped for real auth in multi-user phase

VALID_TX_TYPES = {"income", "expense"}


def _user_account_ids():
    """Return account IDs that belong to the default user."""
    return [a.id for a in Account.query.filter_by(user_id=DEFAULT_USER_ID).all()]


def _validate_tx_fields(data, require_all=True):
    """
    Validate transaction fields.  Pass require_all=False for partial updates.
    Returns (errors_dict, parsed_amount, parsed_date).
    Caller should check `if errors` and return 400.
    """
    errors = {}

    # --- type ---
    tx_type = data.get("type")
    if tx_type is not None:
        if tx_type not in VALID_TX_TYPES:
            errors["type"] = "Must be 'income' or 'expense'."
    elif require_all:
        errors["type"] = "Required."

    # --- amount ---
    raw_amount = data.get("amount")
    parsed_amount = None
    if raw_amount is not None:
        try:
            parsed_amount = float(raw_amount)
            if parsed_amount <= 0:
                errors["amount"] = "Must be greater than 0."
        except (TypeError, ValueError):
            errors["amount"] = "Must be a valid number."
    elif require_all:
        errors["amount"] = "Required."

    # --- date ---
    raw_date = data.get("date")
    parsed_date = None
    if raw_date is not None:
        try:
            parsed_date = date.fromisoformat(raw_date)
        except (ValueError, TypeError):
            errors["date"] = "Must be a valid date in YYYY-MM-DD format."
    elif require_all:
        parsed_date = date.today()   # default only on create

    return errors, parsed_amount, parsed_date


@transactions_bp.get("/")
def list_transactions():
    account_ids = _user_account_ids()
    q = Transaction.query.filter(Transaction.account_id.in_(account_ids))

    # Optional filters
    category_id = request.args.get("category_id", type=int)
    tx_type = request.args.get("type")
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    limit = request.args.get("limit", type=int)

    if category_id:
        q = q.filter_by(category_id=category_id)
    if tx_type in ("income", "expense"):
        q = q.filter_by(type=tx_type)
    if month and year:
        from sqlalchemy import extract
        q = q.filter(
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
    elif year:
        from sqlalchemy import extract
        q = q.filter(extract("year", Transaction.date) == year)

    q = q.order_by(Transaction.date.desc(), Transaction.id.desc())
    if limit:
        q = q.limit(limit)

    return jsonify([t.to_dict() for t in q.all()])


@transactions_bp.post("/")
def create_transaction():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    errors, parsed_amount, parsed_date = _validate_tx_fields(data, require_all=True)
    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    account_ids = _user_account_ids()
    account_id = data.get("account_id")
    if account_id not in account_ids:
        return jsonify({"error": "Account not found"}), 404

    tx = Transaction(
        account_id=account_id,
        category_id=data.get("category_id"),
        amount=parsed_amount,
        type=data["type"],
        description=data.get("description", ""),
        date=parsed_date,
    )
    db.session.add(tx)

    # Update account balance
    account = db.session.get(Account, account_id)
    if tx.type == "income":
        account.balance += tx.amount
    else:
        account.balance -= tx.amount

    db.session.commit()
    return jsonify(tx.to_dict()), 201


@transactions_bp.get("/<int:tx_id>")
def get_transaction(tx_id):
    account_ids = _user_account_ids()
    tx = Transaction.query.filter(
        Transaction.id == tx_id,
        Transaction.account_id.in_(account_ids)
    ).first_or_404()
    return jsonify(tx.to_dict())


@transactions_bp.put("/<int:tx_id>")
def update_transaction(tx_id):
    account_ids = _user_account_ids()
    tx = Transaction.query.filter(
        Transaction.id == tx_id,
        Transaction.account_id.in_(account_ids)
    ).first_or_404()

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    errors, parsed_amount, parsed_date = _validate_tx_fields(data, require_all=False)
    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    # Reverse old balance effect
    account = db.session.get(Account, tx.account_id)
    if tx.type == "income":
        account.balance -= tx.amount
    else:
        account.balance += tx.amount

    # Apply updates
    if "category_id" in data:
        tx.category_id = data["category_id"]
    if parsed_amount is not None:
        tx.amount = parsed_amount
    if "type" in data:
        tx.type = data["type"]
    if "description" in data:
        tx.description = data["description"]
    if parsed_date is not None:
        tx.date = parsed_date

    # Re-apply new balance effect
    if tx.type == "income":
        account.balance += tx.amount
    else:
        account.balance -= tx.amount

    db.session.commit()
    return jsonify(tx.to_dict())


@transactions_bp.delete("/<int:tx_id>")
def delete_transaction(tx_id):
    account_ids = _user_account_ids()
    tx = Transaction.query.filter(
        Transaction.id == tx_id,
        Transaction.account_id.in_(account_ids)
    ).first_or_404()

    # Reverse balance effect
    account = db.session.get(Account, tx.account_id)
    if tx.type == "income":
        account.balance -= tx.amount
    else:
        account.balance += tx.amount

    db.session.delete(tx)
    db.session.commit()
    return jsonify({"deleted": tx_id})
