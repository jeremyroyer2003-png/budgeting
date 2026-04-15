from datetime import datetime, date
from ..extensions import db


class Goal(db.Model):
    __tablename__ = "goal"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    # savings, investment, debt_payoff, purchase
    type = db.Column(db.String(50), nullable=False, default="savings")
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    monthly_target = db.Column(db.Float)   # how much to contribute per month
    target_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def progress_pct(self):
        if self.target_amount == 0:
            return 100.0
        return round(min(self.current_amount / self.target_amount * 100, 100), 1)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.type,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "monthly_target": self.monthly_target,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "is_active": self.is_active,
            "notes": self.notes,
            "progress_pct": self.progress_pct(),
            "created_at": self.created_at.isoformat(),
        }
