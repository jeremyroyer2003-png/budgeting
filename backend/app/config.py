import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, '..', 'budgeting.db')}"
    )

    # ── JWT ────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)   # long-lived for dev comfort

    # ── Plaid ──────────────────────────────────────────────────────────────
    # All three vars must be set to enable the Plaid integration.
    # Leave them unset and the /api/plaid/* routes return a 503 gracefully.
    PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID")
    PLAID_SECRET    = os.environ.get("PLAID_SECRET")
    # sandbox | development | production
    PLAID_ENV       = os.environ.get("PLAID_ENV", "sandbox")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-key-long-enough-for-hs256"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


config = {
    "default": Config,
    "testing": TestingConfig,
}
