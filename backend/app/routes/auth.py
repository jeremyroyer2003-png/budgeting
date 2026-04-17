"""
auth.py — Registration, login, and profile endpoints.

Public:
  POST /api/auth/register  — create account, returns token
  POST /api/auth/login     — verify credentials, returns token

Protected (JWT required):
  GET  /api/auth/me        — return current user profile
  PUT  /api/auth/me        — update name or password
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required

from ..extensions import db
from ..models import User
from ..utils.auth import current_user_id

auth_bp = Blueprint("auth", __name__)

_MIN_PASSWORD_LEN = 8


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    errors = {}

    name = (data.get("name") or "").strip()
    if not name:
        errors["name"] = "Required."

    email = (data.get("email") or "").strip().lower()
    if not email:
        errors["email"] = "Required."
    elif "@" not in email:
        errors["email"] = "Must be a valid email address."

    password = data.get("password") or ""
    if not password:
        errors["password"] = "Required."
    elif len(password) < _MIN_PASSWORD_LEN:
        errors["password"] = f"Must be at least {_MIN_PASSWORD_LEN} characters."

    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()}), 201


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token, "user": user.to_dict()})


# ── Current user ──────────────────────────────────────────────────────────────

@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, current_user_id())
    if not user:
        return jsonify({"error": "User not found."}), 404
    return jsonify(user.to_dict())


@auth_bp.put("/me")
@jwt_required()
def update_me():
    user = db.session.get(User, current_user_id())
    if not user:
        return jsonify({"error": "User not found."}), 404

    data = request.get_json() or {}

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"error": "Validation failed", "fields": {"name": "Cannot be empty."}}), 400
        user.name = name

    if "password" in data:
        pw = data["password"]
        if len(pw) < _MIN_PASSWORD_LEN:
            return jsonify({"error": "Validation failed",
                            "fields": {"password": f"Must be at least {_MIN_PASSWORD_LEN} characters."}}), 400
        user.set_password(pw)

    db.session.commit()
    return jsonify(user.to_dict())
