from datetime import datetime
from ..extensions import db


class Account(db.Model):
    __tablename__ = "account"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    # checking, savings, investment, credit, cash
    type = db.Column(db.String(50), nullable=False, default="checking")
    balance = db.Column(db.Float, default=0.0)
    institution = db.Column(db.String(255))
    account_number_last4 = db.Column(db.String(4))
    # Integration metadata — populated when connected via Plaid/Flinks
    is_connected = db.Column(db.Boolean, default=False)
    provider = db.Column(db.String(50), default="manual")  # manual, mock, plaid, flinks
    provider_account_id = db.Column(db.String(255))        # external ID from provider
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", backref="account", lazy="dynamic", cascade="all, delete-orphan")
    recurring_transactions = db.relationship("RecurringTransaction", backref="account", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "balance": self.balance,
            "institution": self.institution,
            "account_number_last4": self.account_number_last4,
            "is_connected": self.is_connected,
            "provider": self.provider,
            "created_at": self.created_at.isoformat(),
        }
