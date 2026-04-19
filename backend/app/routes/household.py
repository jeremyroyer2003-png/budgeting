"""
household.py routes — couple/family shared budgeting.
"""

from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func, extract
from ..extensions import db
from ..models import Account, Transaction
from ..models.household import Household, HouseholdMember, HouseholdInvite
from ..models.user import User
from ..utils.auth import current_user_id

household_bp = Blueprint("household", __name__)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_membership(uid):
    """Return (household, member) or (None, None) for the given user."""
    member = HouseholdMember.query.filter_by(user_id=uid).first()
    if not member:
        return None, None
    return member.household, member


def _member_spending(user_id, months=1):
    """Return last-N-month income/expense totals for a user."""
    today = date.today()
    account_ids = [a.id for a in Account.query.filter_by(user_id=user_id).all()]
    if not account_ids:
        return {"income": 0.0, "expense": 0.0}

    month_list = []
    m, y = today.month, today.year
    for _ in range(months):
        month_list.append((m, y))
        m -= 1
        if m == 0:
            m, y = 12, y - 1

    def total(tx_type):
        result = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == tx_type,
            db.or_(
                *[
                    db.and_(
                        extract("month", Transaction.date) == mm,
                        extract("year",  Transaction.date) == yy,
                    )
                    for mm, yy in month_list
                ]
            ),
        ).scalar()
        return round(float(result or 0) / months, 2)

    return {"income": total("income"), "expense": total("expense")}


# ── Routes ────────────────────────────────────────────────────────────────────

@household_bp.get("/me")
@jwt_required()
def get_my_household():
    uid = current_user_id()
    household, member = _get_membership(uid)
    if not household:
        return jsonify(None), 200

    members_data = []
    for m in household.members.all():
        spending = _member_spending(m.user_id)
        d = m.to_dict()
        d["income_monthly"]  = spending["income"]
        d["expense_monthly"] = spending["expense"]
        members_data.append(d)

    pending_invites = [
        i.to_dict() for i in household.invites.filter_by(status="pending").all()
    ]

    return jsonify({
        "household":      household.to_dict(),
        "my_role":        member.role,
        "members":        members_data,
        "pending_invites": pending_invites if member.role == "owner" else [],
    })


@household_bp.post("/")
@jwt_required()
def create_household():
    uid  = current_user_id()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Household name is required"}), 400

    # Must not already be in one
    if HouseholdMember.query.filter_by(user_id=uid).first():
        return jsonify({"error": "You are already in a household"}), 409

    hh = Household(name=name, owner_id=uid)
    db.session.add(hh)
    db.session.flush()

    db.session.add(HouseholdMember(household_id=hh.id, user_id=uid, role="owner"))
    db.session.commit()
    return jsonify(hh.to_dict(include_members=True)), 201


@household_bp.post("/invite")
@jwt_required()
def invite_member():
    uid  = current_user_id()
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    household, member = _get_membership(uid)
    if not household or member.role != "owner":
        return jsonify({"error": "Only the household owner can invite members"}), 403

    # Don't invite someone already in this household
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        already = HouseholdMember.query.filter_by(
            user_id=existing_user.id, household_id=household.id
        ).first()
        if already:
            return jsonify({"error": "This user is already in your household"}), 409

    # Reuse pending invite if one exists
    invite = HouseholdInvite.query.filter_by(
        household_id=household.id, invitee_email=email, status="pending"
    ).first()
    if not invite:
        invite = HouseholdInvite(household_id=household.id, invitee_email=email)
        db.session.add(invite)
        db.session.commit()

    return jsonify({
        "invite":     invite.to_dict(),
        "accept_url": f"#accept-invite/{invite.token}",
    }), 201


@household_bp.post("/invite/<token>/accept")
@jwt_required()
def accept_invite(token):
    uid    = current_user_id()
    invite = HouseholdInvite.query.filter_by(token=token, status="pending").first_or_404()

    user = User.query.get(uid)
    if user.email.lower() != invite.invitee_email.lower():
        return jsonify({"error": "This invite was sent to a different email address"}), 403

    if HouseholdMember.query.filter_by(user_id=uid).first():
        return jsonify({"error": "You are already in a household"}), 409

    db.session.add(HouseholdMember(
        household_id=invite.household_id, user_id=uid, role="member"
    ))
    invite.status = "accepted"
    db.session.commit()
    return jsonify({"success": True, "household_id": invite.household_id})


@household_bp.delete("/leave")
@jwt_required()
def leave_household():
    uid = current_user_id()
    household, member = _get_membership(uid)
    if not household:
        return jsonify({"error": "You are not in a household"}), 404

    if member.role == "owner":
        # Transfer ownership to next member, or disband
        others = HouseholdMember.query.filter(
            HouseholdMember.household_id == household.id,
            HouseholdMember.user_id     != uid,
        ).first()
        if others:
            others.role    = "owner"
            household.owner_id = others.user_id
        else:
            db.session.delete(household)
            db.session.commit()
            return jsonify({"success": True, "disbanded": True})

    db.session.delete(member)
    db.session.commit()
    return jsonify({"success": True})


@household_bp.delete("/members/<int:member_id>")
@jwt_required()
def remove_member(member_id):
    uid = current_user_id()
    _, my_membership = _get_membership(uid)
    if not my_membership or my_membership.role != "owner":
        return jsonify({"error": "Only the owner can remove members"}), 403

    target = HouseholdMember.query.filter_by(
        id=member_id, household_id=my_membership.household_id
    ).first_or_404()

    if target.user_id == uid:
        return jsonify({"error": "Use /leave to leave the household"}), 400

    db.session.delete(target)
    db.session.commit()
    return jsonify({"success": True})
