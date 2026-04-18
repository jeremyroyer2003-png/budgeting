"""
subscriptions.py — Detected subscription endpoints.

GET /api/subscriptions/         — list all detected subscriptions + summary
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..models import Account
from ..services.subscription_service import detect_subscriptions, subscription_summary
from ..utils.auth import current_user_id

subscriptions_bp = Blueprint("subscriptions", __name__)


@subscriptions_bp.get("/")
@jwt_required()
def list_subscriptions():
    account_ids = [
        a.id for a in Account.query.filter_by(user_id=current_user_id()).all()
    ]
    subs    = detect_subscriptions(account_ids)
    summary = subscription_summary(subs)

    return jsonify({
        "summary":       summary,
        "subscriptions": [_to_dict(s) for s in subs],
    })


def _to_dict(s) -> dict:
    return {
        "key":            s.key,
        "name":           s.name,
        "frequency":      s.frequency,
        "interval_days":  s.interval_days,
        "monthly_cost":   s.monthly_cost,
        "last_amount":    s.last_amount,
        "last_date":      s.last_date.isoformat(),
        "next_estimated": s.next_estimated.isoformat(),
        "occurrences":    s.occurrences,
        "price_changed":  s.price_changed,
        "price_history":  s.price_history,
        "category_name":  s.category_name,
    }
