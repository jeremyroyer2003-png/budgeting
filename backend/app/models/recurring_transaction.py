from datetime import datetime, date
from ..extensions import db


class RecurringTransaction(db.Model):
    __tablename__ = "recurring_transaction"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # income or expense
    description = db.Column(db.String(500))
    # daily, weekly, biweekly, monthly, yearly
    frequency = db.Column(db.String(20), nullable=False, default="monthly")
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date)
    next_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    generated_transactions = db.relationship("Transaction", backref="recurring_source", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "account_id": self.account_id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "amount": self.amount,
            "type": self.type,
            "description": self.description,
            "frequency": self.frequency,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "next_date": self.next_date.isoformat() if self.next_date else None,
            "is_active": self.is_active,
        }
