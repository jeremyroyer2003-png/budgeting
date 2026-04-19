"""
household.py — Models for couple/family shared budgeting.

A Household groups users who share visibility of each other's accounts.
One user is the "owner"; others join via invite tokens.
"""

import secrets
from datetime import datetime
from ..extensions import db


class Household(db.Model):
    __tablename__ = "household"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    owner_id   = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship("HouseholdMember", backref="household",
                               lazy="dynamic", cascade="all, delete-orphan")
    invites = db.relationship("HouseholdInvite", backref="household",
                               lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, include_members=False):
        d = {
            "id":         self.id,
            "name":       self.name,
            "owner_id":   self.owner_id,
            "created_at": self.created_at.isoformat(),
        }
        if include_members:
            d["members"] = [m.to_dict() for m in self.members.all()]
        return d


class HouseholdMember(db.Model):
    __tablename__ = "household_member"

    id           = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    user_id      = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role         = db.Column(db.String(20), default="member")   # owner | member
    joined_at    = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id":           self.id,
            "household_id": self.household_id,
            "user_id":      self.user_id,
            "user_name":    self.user.name  if self.user else None,
            "user_email":   self.user.email if self.user else None,
            "role":         self.role,
            "joined_at":    self.joined_at.isoformat(),
        }


class HouseholdInvite(db.Model):
    __tablename__ = "household_invite"

    id           = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    invitee_email = db.Column(db.String(255), nullable=False)
    token        = db.Column(db.String(64), unique=True, nullable=False,
                             default=lambda: secrets.token_urlsafe(32))
    status       = db.Column(db.String(20), default="pending")   # pending | accepted | declined
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":            self.id,
            "household_id":  self.household_id,
            "invitee_email": self.invitee_email,
            "token":         self.token,
            "status":        self.status,
            "created_at":    self.created_at.isoformat(),
        }
