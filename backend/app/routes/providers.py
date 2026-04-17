"""
providers.py — Universal bank connection API.

Endpoints:
  GET  /api/providers/institutions          — search institutions (CA + US)
  GET  /api/providers/institutions/<id>     — single institution + which provider
  GET  /api/providers/connections           — list all connected accounts (all providers)
  POST /api/providers/connect               — initiate Link flow (returns link_token or redirect URL)
  POST /api/providers/exchange              — exchange one-time token → store connection + sync
  POST /api/providers/sync                  — re-sync all connections for this user
  DELETE /api/providers/connections/<id>    — remove a connection
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models.provider_connection import ProviderConnection
from ..integrations.institution_registry import (
    get_institution, search_institutions, list_institutions
)
from ..integrations.provider_router import ProviderRouter, ProviderUnavailableError
from ..utils.auth import current_user_id

providers_bp = Blueprint("providers", __name__)


def _router() -> ProviderRouter:
    return ProviderRouter(current_app.config)


# ── Institution search ─────────────────────────────────────────────────────────

@providers_bp.get("/institutions")
@jwt_required()
def list_all_institutions():
    """
    GET /api/providers/institutions?query=td&country=CA

    Returns institutions matching the optional search query.
    Each result includes which provider will be used and whether
    that provider is currently configured.
    """
    query   = request.args.get("query", "").strip()
    country = request.args.get("country", None)

    if query:
        institutions = search_institutions(query, country)
    else:
        institutions = list_institutions(country)

    router = _router()
    return jsonify([
        {
            "id":            inst.id,
            "name":          inst.name,
            "country":       inst.country,
            "category":      inst.category,
            "provider":      inst.provider,
            "fallback":      inst.fallback,
            "active_provider": router.provider_for_institution(inst.id),
            "logo_key":      inst.logo_key,
        }
        for inst in institutions
    ])


@providers_bp.get("/institutions/<institution_id>")
@jwt_required()
def get_institution_detail(institution_id: str):
    """Return a single institution with provider status."""
    inst = get_institution(institution_id)
    if not inst:
        return jsonify({"error": f"Institution '{institution_id}' not found."}), 404

    router = _router()
    return jsonify({
        "id":              inst.id,
        "name":            inst.name,
        "country":         inst.country,
        "category":        inst.category,
        "provider":        inst.provider,
        "fallback":        inst.fallback,
        "active_provider": router.provider_for_institution(inst.id),
    })


# ── Connection management ──────────────────────────────────────────────────────

@providers_bp.get("/connections")
@jwt_required()
def list_connections():
    """Return all provider connections for this user."""
    conns = ProviderConnection.query.filter_by(user_id=current_user_id()).all()
    return jsonify([c.to_dict() for c in conns])


@providers_bp.delete("/connections/<int:conn_id>")
@jwt_required()
def delete_connection(conn_id: int):
    """Remove a provider connection."""
    conn = ProviderConnection.query.filter_by(
        id=conn_id, user_id=current_user_id()
    ).first_or_404()
    db.session.delete(conn)
    db.session.commit()
    return jsonify({"deleted": conn_id})


# ── Link initiation ────────────────────────────────────────────────────────────

@providers_bp.post("/connect")
@jwt_required()
def initiate_connect():
    """
    Step 1 of the Link flow.

    Body: { "institution_id": "desjardins" }

    Returns the appropriate link_token or redirect URL for the chosen provider.
    The frontend uses this to open the correct Link UI.
    """
    data           = request.get_json() or {}
    institution_id = data.get("institution_id")
    if not institution_id:
        return jsonify({"error": "institution_id is required"}), 400

    router        = _router()
    provider_name = router.provider_for_institution(institution_id)

    try:
        if provider_name == "plaid":
            return _plaid_link_token(institution_id)
        if provider_name == "flinks":
            return _flinks_connect_url(institution_id)
        if provider_name == "wealthica":
            return _wealthica_connect_url(institution_id)
    except ProviderUnavailableError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"error": f"Provider '{provider_name}' is not yet implemented."}), 503


# ── Token exchange ─────────────────────────────────────────────────────────────

@providers_bp.post("/exchange")
@jwt_required()
def exchange_token():
    """
    Step 2 of the Link flow.

    Body: {
      "provider":        "plaid" | "flinks" | "wealthica",
      "institution_id":  "td_ca",
      "public_token":    "...",   // Plaid
      "login_id":        "...",   // Flinks
      "oauth_token":     "...",   // Wealthica
    }
    """
    data           = request.get_json() or {}
    provider_name  = data.get("provider")
    institution_id = data.get("institution_id")

    if not provider_name or not institution_id:
        return jsonify({"error": "provider and institution_id are required"}), 400

    try:
        if provider_name == "plaid":
            public_token = data.get("public_token")
            if not public_token:
                return jsonify({"error": "public_token is required for Plaid"}), 400
            return _plaid_exchange(institution_id, public_token)

        if provider_name == "flinks":
            return jsonify({"error": "Flinks exchange not yet implemented — credentials required"}), 503

        if provider_name == "wealthica":
            return jsonify({"error": "Wealthica exchange not yet implemented — credentials required"}), 503

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    return jsonify({"error": f"Unknown provider: {provider_name}"}), 400


# ── Re-sync ────────────────────────────────────────────────────────────────────

@providers_bp.post("/sync")
@jwt_required()
def sync_all():
    """Re-sync all connections for this user."""
    conns = ProviderConnection.query.filter_by(user_id=current_user_id()).all()
    if not conns:
        return jsonify({"message": "No connections found."}), 200

    results = []
    for conn in conns:
        try:
            if conn.provider == "plaid":
                from ..routes.plaid import _sync_connection as _plaid_sync
                r = _plaid_sync(conn)
                results.append({"id": conn.id, "provider": "plaid", **r})
            else:
                results.append({"id": conn.id, "provider": conn.provider, "message": "sync not yet implemented"})
        except Exception as exc:
            results.append({"id": conn.id, "provider": conn.provider, "error": str(exc)})

    return jsonify(results)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _plaid_link_token(institution_id: str):
    """Delegate to existing Plaid route logic."""
    from ..routes.plaid import create_link_token as _plaid_route
    return _plaid_route()


def _plaid_exchange(institution_id: str, public_token: str):
    """Delegate to existing Plaid exchange logic (keeps existing plaid.py working)."""
    from ..routes.plaid import exchange_token as _plaid_exchange_route
    return _plaid_exchange_route()


def _flinks_connect_url(institution_id: str):
    flinks_url = current_app.config.get("FLINKS_API_URL")
    if not flinks_url:
        return jsonify({
            "error": "Flinks is not configured. Set FLINKS_API_URL in your environment."
        }), 503
    return jsonify({
        "provider":    "flinks",
        "connect_url": f"{flinks_url}/Authorize",
        "institution": institution_id,
    })


def _wealthica_connect_url(institution_id: str):
    client_id = current_app.config.get("WEALTHICA_CLIENT_ID")
    if not client_id:
        return jsonify({
            "error": "Wealthica is not configured. Set WEALTHICA_CLIENT_ID in your environment."
        }), 503
    return jsonify({
        "provider":    "wealthica",
        "connect_url": f"https://app.wealthica.com/oauth/authorize?client_id={client_id}",
        "institution": institution_id,
    })
