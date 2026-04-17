from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    __tablename__ = "user"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    name          = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)   # nullable for migration safety
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    accounts = db.relationship("Account", backref="user", lazy="dynamic", cascade="all, delete-orphan")
    budgets  = db.relationship("Budget",  backref="user", lazy="dynamic", cascade="all, delete-orphan")
    goals    = db.relationship("Goal",    backref="user", lazy="dynamic", cascade="all, delete-orphan")
    alerts   = db.relationship("Alert",   backref="user", lazy="dynamic", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }
