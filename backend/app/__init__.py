from flask import Flask
from .config import config
from .extensions import db, cors


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register all blueprints
    from .routes import (
        transactions_bp, categories_bp, budgets_bp,
        goals_bp, alerts_bp, accounts_bp, dashboard_bp, recurring_bp
    )
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(categories_bp, url_prefix="/api/categories")
    app.register_blueprint(budgets_bp, url_prefix="/api/budgets")
    app.register_blueprint(goals_bp, url_prefix="/api/goals")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(recurring_bp, url_prefix="/api/recurring")

    with app.app_context():
        db.create_all()

    return app
