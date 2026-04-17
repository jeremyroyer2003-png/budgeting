"""
provider_connection.py — Universal bank connection model.

Replaces the Plaid-specific PlaidConnection with a provider-agnostic model
that works for Plaid, Flinks, and Wealthica under the same table.

access_token is stored encrypted (AES via utils.encryption).
The raw token is never exposed through to_dict().
"""

from datetime import datetime
from ..extensions import db
from ..utils.encryption import encrypt_token, decrypt_token


class ProviderConnection(db.Model):
    __tablename__ = "provider_connection"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Which provider manages this connection
    provider         = db.Column(db.String(20), nullable=False)  # plaid | flinks | wealthica

    # Provider-side identifiers
    item_id          = db.Column(db.String(255), unique=True, nullable=False)
    institution_id   = db.Column(db.String(100))   # our internal slug e.g. "td_ca"
    institution_name = db.Column(db.String(255))

    # Encrypted access token (AES-128-CBC via Fernet)
    _access_token_enc = db.Column("access_token_enc", db.Text, nullable=False)

    # Cursor for incremental sync (Plaid /transactions/sync, Flinks equivalent)
    sync_cursor      = db.Column(db.Text)

    # Connection health
    status           = db.Column(db.String(20), default="active")  # active | error | reauth_required
    error_code       = db.Column(db.String(100))

    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced      = db.Column(db.DateTime)

    # ── Token property (encrypt/decrypt transparently) ─────────────────────

    @property
    def access_token(self) -> str:
        return decrypt_token(self._access_token_enc)

    @access_token.setter
    def access_token(self, plaintext: str) -> None:
        self._access_token_enc = encrypt_token(plaintext)

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Never exposes the access token."""
        return {
            "id":               self.id,
            "provider":         self.provider,
            "item_id":          self.item_id,
            "institution_id":   self.institution_id,
            "institution_name": self.institution_name,
            "status":           self.status,
            "error_code":       self.error_code,
            "last_synced":      self.last_synced.isoformat() if self.last_synced else None,
            "created_at":       self.created_at.isoformat(),
        }
