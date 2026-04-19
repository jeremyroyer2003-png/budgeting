from flask import Flask, jsonify
from .config import config
from .extensions import db, cors, jwt


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    jwt.init_app(app)

    # Return clean JSON on JWT errors instead of HTML
    @jwt.unauthorized_loader
    def unauthorized_response(_reason):
        return jsonify({"error": "Authentication required. Please log in."}), 401

    @jwt.invalid_token_loader
    def invalid_token_response(_reason):
        return jsonify({"error": "Invalid or expired token. Please log in again."}), 401

    @jwt.expired_token_loader
    def expired_token_response(_jwt_header, _jwt_data):
        return jsonify({"error": "Session expired. Please log in again."}), 401

    # Register all blueprints
    from .routes import (
        auth_bp,
        transactions_bp, categories_bp, budgets_bp,
        goals_bp, alerts_bp, accounts_bp, dashboard_bp, recurring_bp,
        plaid_bp, providers_bp, subscriptions_bp,
        insights_bp, household_bp,
    )
    app.register_blueprint(auth_bp,           url_prefix="/api/auth")
    app.register_blueprint(transactions_bp,   url_prefix="/api/transactions")
    app.register_blueprint(categories_bp,     url_prefix="/api/categories")
    app.register_blueprint(budgets_bp,        url_prefix="/api/budgets")
    app.register_blueprint(goals_bp,          url_prefix="/api/goals")
    app.register_blueprint(alerts_bp,         url_prefix="/api/alerts")
    app.register_blueprint(accounts_bp,       url_prefix="/api/accounts")
    app.register_blueprint(dashboard_bp,      url_prefix="/api/dashboard")
    app.register_blueprint(recurring_bp,      url_prefix="/api/recurring")
    app.register_blueprint(plaid_bp,          url_prefix="/api/plaid")
    app.register_blueprint(providers_bp,      url_prefix="/api/providers")
    app.register_blueprint(subscriptions_bp,  url_prefix="/api/subscriptions")
    app.register_blueprint(insights_bp,       url_prefix="/api/insights")
    app.register_blueprint(household_bp,      url_prefix="/api/household")

    with app.app_context():
        db.create_all()

    return app
