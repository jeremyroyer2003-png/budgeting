from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import Alert
from ..services.alert_service import generate_alerts
from ..utils.auth import current_user_id

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("/")
@jwt_required()
def list_alerts():
    show_read = request.args.get("show_read", "false").lower() == "true"
    q = Alert.query.filter_by(user_id=current_user_id())
    if not show_read:
        q = q.filter_by(is_read=False)
    alerts = q.order_by(Alert.created_at.desc()).all()
    return jsonify([a.to_dict() for a in alerts])


@alerts_bp.post("/<int:alert_id>/read")
@jwt_required()
def mark_read(alert_id):
    alert = Alert.query.filter_by(id=alert_id, user_id=current_user_id()).first_or_404()
    alert.is_read = True
    db.session.commit()
    return jsonify(alert.to_dict())


@alerts_bp.post("/read-all")
@jwt_required()
def mark_all_read():
    Alert.query.filter_by(user_id=current_user_id(), is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})


@alerts_bp.post("/generate")
@jwt_required()
def run_generate_alerts():
    """Trigger alert generation based on current budget and goal state."""
    count = generate_alerts(current_user_id())
    return jsonify({"generated": count})
