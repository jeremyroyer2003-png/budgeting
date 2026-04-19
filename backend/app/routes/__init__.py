from .auth import auth_bp
from .transactions import transactions_bp
from .categories import categories_bp
from .budgets import budgets_bp
from .goals import goals_bp
from .alerts import alerts_bp
from .accounts import accounts_bp
from .dashboard import dashboard_bp
from .recurring import recurring_bp
from .plaid import plaid_bp
from .providers import providers_bp
from .subscriptions import subscriptions_bp
from .insights import insights_bp
from .household import household_bp

__all__ = [
    "auth_bp",
    "transactions_bp", "categories_bp", "budgets_bp", "goals_bp",
    "alerts_bp", "accounts_bp", "dashboard_bp", "recurring_bp",
    "plaid_bp", "providers_bp", "subscriptions_bp",
    "insights_bp", "household_bp",
]
