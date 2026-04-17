"""
Plaid sandbox integration routes.

Endpoints:
  POST /api/plaid/link-token      — create a Plaid Link token for the frontend
  POST /api/plaid/exchange-token  — exchange public_token → access_token, sync data
  POST /api/plaid/sync            — re-sync all connected Plaid items for this user
  GET  /api/plaid/connections     — list connected bank items
  DELETE /api/plaid/connections/<id> — remove a connection and its imported accounts

All endpoints return a clear 503 when Plaid is not configured so the rest of
the app continues to work normally.
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, request, jsonify
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Account, Category, Transaction
from ..models.plaid_connection import PlaidConnection
from ..integrations.plaid_provider import PlaidProvider, PLAID_AVAILABLE, build_plaid_client
from ..utils.auth import current_user_id

plaid_bp = Blueprint("plaid", __name__)

# How many days of history to pull on the first sync
INITIAL_SYNC_DAYS = 30


# ── Helpers ────────────────────────────────────────────────────────────────

def _plaid_configured() -> bool:
    return bool(
        current_app.config.get("PLAID_CLIENT_ID")
        and current_app.config.get("PLAID_SECRET")
    )

def _not_configured_response():
    return jsonify({
        "error": (
            "Plaid is not configured. "
            "Set PLAID_CLIENT_ID and PLAID_SECRET in your environment, "
            "then restart the backend."
        )
    }), 503

def _sdk_missing_response():
    return jsonify({
        "error": "plaid-python SDK is not installed. Run: pip install plaid-python"
    }), 503

def _get_plaid_client():
    """Build an authenticated Plaid client from app config."""
    return build_plaid_client(
        current_app.config["PLAID_CLIENT_ID"],
        current_app.config["PLAID_SECRET"],
        current_app.config.get("PLAID_ENV", "sandbox"),
    )

def _find_category_id(hint: str | None, tx_type: str) -> int | None:
    """Look up a local Category by name hint and type."""
    if not hint:
        return None
    cat = Category.query.filter_by(name=hint, type=tx_type).first()
    if not cat:
        # Fallback: any category of the right type
        cat = Category.query.filter_by(type=tx_type).first()
    return cat.id if cat else None


# ── Routes ─────────────────────────────────────────────────────────────────

@plaid_bp.post("/link-token")
@jwt_required()
def create_link_token():
    """
    Step 1 of the Link flow: generate a short-lived link_token for the frontend.

    The frontend passes this token to Plaid.create({ token: ... }) to open
    the Plaid Link UI where the user authenticates with their bank.
    """
    if not PLAID_AVAILABLE:
        return _sdk_missing_response()
    if not _plaid_configured():
        return _not_configured_response()

    try:
        # Import here so the rest of the module never fails when Plaid is absent
        from plaid.model.link_token_create_request import LinkTokenCreateRequest
        from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
        from plaid.model.country_code import CountryCode
        from plaid.model.products import Products

        client = _get_plaid_client()
        link_request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="ClearBudget",
            country_codes=[CountryCode("US"), CountryCode("CA")],
            language="en",
            # client_user_id ties the Link session to our user.
            # Use the real user's ID/UUID here in production.
            user=LinkTokenCreateRequestUser(client_user_id=str(current_user_id())),
        )
        response = client.link_token_create(link_request)
        return jsonify({"link_token": response.link_token})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@plaid_bp.post("/exchange-token")
@jwt_required()
def exchange_token():
    """
    Step 2 of the Link flow: exchange the one-time public_token returned by
    Plaid Link for a permanent access_token, then immediately sync accounts
    and recent transactions into the app.

    Body: { "public_token": "public-sandbox-..." }
    """
    if not PLAID_AVAILABLE:
        return _sdk_missing_response()
    if not _plaid_configured():
        return _not_configured_response()

    data = request.get_json() or {}
    public_token = data.get("public_token")
    if not public_token:
        return jsonify({"error": "public_token is required"}), 400

    try:
        from plaid.model.item_public_token_exchange_request import (
            ItemPublicTokenExchangeRequest,
        )
        from plaid.model.item_get_request import ItemGetRequest

        client = _get_plaid_client()

        # Exchange public_token → access_token
        exchange_resp = client.item_public_token_exchange(
            ItemPublicTokenExchangeRequest(public_token=public_token)
        )
        access_token = exchange_resp.access_token
        item_id      = exchange_resp.item_id

        # Fetch institution name for display
        try:
            item_resp        = client.item_get(ItemGetRequest(access_token=access_token))
            institution_id   = item_resp.item.institution_id
            institution_name = institution_id  # will be a real name in production
        except Exception:
            institution_name = "Connected Bank"

        # Upsert PlaidConnection (re-connecting the same bank just refreshes the token)
        connection = PlaidConnection.query.filter_by(item_id=item_id).first()
        if connection:
            connection.access_token     = access_token
            connection.institution_name = institution_name
        else:
            connection = PlaidConnection(
                user_id          = current_user_id(),
                item_id          = item_id,
                access_token     = access_token,
                institution_name = institution_name,
            )
            db.session.add(connection)
        db.session.commit()

        # Sync accounts + recent transactions right away
        result = _sync_connection(connection)
        return jsonify(result), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@plaid_bp.post("/sync")
@jwt_required()
def sync_all():
    """
    Re-sync every PlaidConnection for this user.

    Call this on a schedule (e.g. nightly) to keep transactions current.

    PRODUCTION NOTE: Use Plaid webhooks + /transactions/sync (cursor-based)
    instead of polling with date ranges to avoid re-importing duplicates.
    """
    if not PLAID_AVAILABLE:
        return _sdk_missing_response()
    if not _plaid_configured():
        return _not_configured_response()

    connections = PlaidConnection.query.filter_by(user_id=current_user_id()).all()
    if not connections:
        return jsonify({"message": "No Plaid connections found. Connect a bank first."}), 200

    totals = {"accounts_imported": 0, "transactions_imported": 0, "connections_synced": 0}
    errors = []

    for conn in connections:
        try:
            result = _sync_connection(conn)
            totals["accounts_imported"]    += result["accounts_imported"]
            totals["transactions_imported"] += result["transactions_imported"]
            totals["connections_synced"]   += 1
        except Exception as exc:
            errors.append({"item_id": conn.item_id, "error": str(exc)})

    totals["errors"] = errors
    return jsonify(totals), 200


@plaid_bp.get("/connections")
@jwt_required()
def list_connections():
    """List all Plaid-connected bank items for this user."""
    connections = PlaidConnection.query.filter_by(user_id=current_user_id()).all()
    return jsonify([c.to_dict() for c in connections])


@plaid_bp.delete("/connections/<int:conn_id>")
@jwt_required()
def delete_connection(conn_id: int):
    """
    Remove a Plaid connection.

    PRODUCTION NOTE: Also call /item/remove on the Plaid API to revoke the
    access_token and stop Plaid from holding the bank credentials.
    """
    conn = PlaidConnection.query.filter_by(
        id=conn_id, user_id=current_user_id()
    ).first_or_404()
    db.session.delete(conn)
    db.session.commit()
    return jsonify({"deleted": conn_id})


# ── Core sync logic ────────────────────────────────────────────────────────

def _sync_connection(connection: PlaidConnection) -> dict:
    """
    Pull accounts and recent transactions from Plaid and upsert into local DB.

    Returns a summary dict with counts.
    """
    provider = PlaidProvider()
    provider.authenticate({
        "client_id": current_app.config["PLAID_CLIENT_ID"],
        "secret":    current_app.config["PLAID_SECRET"],
        "env":       current_app.config.get("PLAID_ENV", "sandbox"),
    })

    access_token = connection.access_token

    # ── 1. Accounts ────────────────────────────────────────────────────────
    remote_accounts = provider.get_accounts(access_token)
    plaid_to_local: dict[str, int] = {}   # provider_account_id → local account.id
    accounts_imported = 0

    for remote in remote_accounts:
        existing = Account.query.filter_by(
            provider="plaid",
            provider_account_id=remote.provider_account_id,
        ).first()

        if existing:
            # Refresh balance on re-sync
            existing.balance = remote.balance
            local_acct = existing
        else:
            local_acct = Account(
                user_id              = connection.user_id,
                name                 = remote.name,
                type                 = remote.type,
                balance              = remote.balance,
                institution          = connection.institution_name or remote.institution,
                account_number_last4 = remote.account_number_last4,
                is_connected         = True,
                provider             = "plaid",
                provider_account_id  = remote.provider_account_id,
            )
            db.session.add(local_acct)
            accounts_imported += 1

        db.session.flush()
        plaid_to_local[remote.provider_account_id] = local_acct.id

    # ── 2. Transactions ────────────────────────────────────────────────────
    end_date   = date.today()
    start_date = end_date - timedelta(days=INITIAL_SYNC_DAYS)

    remote_txns = provider.get_transactions(access_token, None, start_date, end_date)
    transactions_imported = 0

    for remote in remote_txns:
        local_account_id = plaid_to_local.get(remote.provider_account_id)
        if not local_account_id:
            continue  # transaction belongs to an account we didn't map

        # Skip if we already have this exact Plaid transaction (simple dedup).
        # In production use a dedicated provider_transaction_id column instead.
        already = Transaction.query.filter_by(
            account_id  = local_account_id,
            description = remote.description,
            date        = remote.date,
            amount      = remote.amount,
            type        = remote.type,
        ).first()
        if already:
            continue

        category_id = _find_category_id(remote.category_hint, remote.type)
        txn = Transaction(
            account_id  = local_account_id,
            category_id = category_id,
            amount      = remote.amount,
            type        = remote.type,
            description = remote.description,
            date        = remote.date,
        )
        db.session.add(txn)
        transactions_imported += 1

    connection.last_synced = datetime.utcnow()
    db.session.commit()

    return {
        "accounts_imported":    accounts_imported,
        "transactions_imported": transactions_imported,
        "institution":          connection.institution_name,
    }
