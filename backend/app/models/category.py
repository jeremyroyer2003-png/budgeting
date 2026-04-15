from ..extensions import db


class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    type = db.Column(db.String(20), nullable=False)  # income or expense
    color = db.Column(db.String(7), default="#6366F1")
    icon = db.Column(db.String(50), default="tag")
    # System categories are seeded defaults and cannot be deleted
    is_system = db.Column(db.Boolean, default=False)

    transactions = db.relationship("Transaction", backref="category", lazy="dynamic")
    budgets = db.relationship("Budget", backref="category", lazy="dynamic")
    alerts = db.relationship("Alert", backref="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "color": self.color,
            "icon": self.icon,
            "is_system": self.is_system,
        }
