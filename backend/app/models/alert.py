from datetime import datetime
from ..extensions import db


class Alert(db.Model):
    __tablename__ = "alert"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # overspending, savings_behind, goal_at_risk, investment_below_target, info
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    # info, warning, critical
    severity = db.Column(db.String(20), nullable=False, default="info")
    is_read = db.Column(db.Boolean, default=False)
    # Optional link to a category (e.g. for an overspending alert)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "severity": self.severity,
            "is_read": self.is_read,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "created_at": self.created_at.isoformat(),
        }
