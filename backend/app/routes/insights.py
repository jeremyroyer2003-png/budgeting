from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models import Account
from ..services.insights_service import compute_peer_comparison
from ..utils.auth import current_user_id

insights_bp = Blueprint("insights", __name__)


@insights_bp.get("/peer-comparison")
@jwt_required()
def peer_comparison():
    uid = current_user_id()
    months = request.args.get("months", 3, type=int)
    months = max(1, min(months, 12))
    account_ids = [a.id for a in Account.query.filter_by(user_id=uid).all()]
    data = compute_peer_comparison(account_ids, months)
    return jsonify(data or {})
