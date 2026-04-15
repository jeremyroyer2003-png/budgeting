from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Alert
from ..services.alert_service import generate_alerts

alerts_bp = Blueprint("alerts", __name__)

DEFAULT_USER_ID = 1


@alerts_bp.get("/")
def list_alerts():
    show_read = request.args.get("show_read", "false").lower() == "true"
    q = Alert.query.filter_by(user_id=DEFAULT_USER_ID)
    if not show_read:
        q = q.filter_by(is_read=False)
    alerts = q.order_by(Alert.created_at.desc()).all()
    return jsonify([a.to_dict() for a in alerts])


@alerts_bp.post("/<int:alert_id>/read")
def mark_read(alert_id):
    alert = Alert.query.filter_by(id=alert_id, user_id=DEFAULT_USER_ID).first_or_404()
    alert.is_read = True
    db.session.commit()
    return jsonify(alert.to_dict())


@alerts_bp.post("/read-all")
def mark_all_read():
    Alert.query.filter_by(user_id=DEFAULT_USER_ID, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})


@alerts_bp.post("/generate")
def run_generate_alerts():
    """Trigger alert generation based on current budget and goal state."""
    count = generate_alerts(DEFAULT_USER_ID)
    return jsonify({"generated": count})
