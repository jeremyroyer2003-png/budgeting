from datetime import datetime
from ..extensions import db


class PlaidConnection(db.Model):
    """
    Stores a Plaid access token for one connected bank item (institution).

    One user can have many PlaidConnections — one per bank they link.
    Each connection can expose multiple accounts.

    PRODUCTION NOTE: access_token must be encrypted at rest before storing.
    Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) or at minimum
    SQLAlchemy-Utils EncryptedType with a key from the environment.
    """
    __tablename__ = "plaid_connection"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # Plaid item_id uniquely identifies the bank connection on Plaid's side
    item_id      = db.Column(db.String(255), unique=True, nullable=False)
    # SANDBOX/DEV ONLY — encrypt this field before going to production
    access_token = db.Column(db.String(255), nullable=False)
    institution_name = db.Column(db.String(255))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced  = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id":               self.id,
            "item_id":          self.item_id,
            "institution_name": self.institution_name,
            "last_synced":      self.last_synced.isoformat() if self.last_synced else None,
            "created_at":       self.created_at.isoformat(),
        }
