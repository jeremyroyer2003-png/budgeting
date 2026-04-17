"""
auth.py — JWT helper used by every protected route.

Usage in a route:
    from flask_jwt_extended import jwt_required
    from ..utils.auth import current_user_id

    @bp.get("/")
    @jwt_required()
    def list_things():
        uid = current_user_id()
        ...
"""
from flask_jwt_extended import get_jwt_identity


def current_user_id() -> int:
    """Return the integer user_id stored in the active JWT."""
    return int(get_jwt_identity())
