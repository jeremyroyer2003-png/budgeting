from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import Alert, Account
from ..services.alert_service import generate_alerts
from ..services.weekly_summary_service import compute_weekly_summary, weekly_alert_message, get_week_bounds
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


@alerts_bp.get("/weekly-summary")
@jwt_required()
def get_weekly_summary():
    uid = current_user_id()
    account_ids = [a.id for a in Account.query.filter_by(user_id=uid).all()]
    summary = compute_weekly_summary(account_ids)
    return jsonify(summary or {})


@alerts_bp.post("/generate-weekly")
@jwt_required()
def generate_weekly_summary():
    """Create a weekly_summary alert if one hasn't been stored for this week yet."""
    uid = current_user_id()
    ws, _ = get_week_bounds()
    cutoff = ws  # don't create a second summary for the same week

    existing = Alert.query.filter(
        Alert.user_id == uid,
        Alert.type == "weekly_summary",
        Alert.created_at >= cutoff,
    ).first()

    if existing:
        return jsonify({"created": False, "message": "Already generated this week"})

    account_ids = [a.id for a in Account.query.filter_by(user_id=uid).all()]
    summary = compute_weekly_summary(account_ids)
    if not summary or summary["tx_count"] == 0:
        return jsonify({"created": False, "message": "No transactions this week"})

    alert = Alert(
        user_id=uid,
        type="weekly_summary",
        severity="info",
        message=weekly_alert_message(summary),
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({"created": True, "alert": alert.to_dict()})
