from datetime import date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import extract, func
from ..extensions import db
from ..models import Transaction, Account, Goal, Alert, Budget, Category
from ..services.budget_service import get_budget_summary
from ..services.goal_service import enrich_goal
from ..utils.auth import current_user_id

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@jwt_required()
def get_dashboard():
    today = date.today()
    month = request.args.get("month", type=int, default=today.month)
    year  = request.args.get("year",  type=int, default=today.year)
    uid   = current_user_id()

    account_ids = [a.id for a in Account.query.filter_by(user_id=uid).all()]

    # --- Income & Expenses for the month ---
    def month_total(tx_type):
        result = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == tx_type,
            extract("month", Transaction.date) == month,
            extract("year",  Transaction.date) == year,
        ).scalar()
        return round(result or 0.0, 2)

    total_income   = month_total("income")
    total_expenses = month_total("expense")
    net            = round(total_income - total_expenses, 2)
    savings_rate   = round((net / total_income * 100) if total_income > 0 else 0.0, 1)

    # --- Account balances ---
    accounts      = Account.query.filter_by(user_id=uid).all()
    total_balance = round(sum(a.balance for a in accounts), 2)

    # --- Spending by category (pie chart) ---
    cat_spending = (
        db.session.query(Category.name, Category.color, func.sum(Transaction.amount).label("total"))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == "expense",
            extract("month", Transaction.date) == month,
            extract("year",  Transaction.date) == year,
        )
        .group_by(Category.id)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    spending_by_category = [
        {"name": r.name, "color": r.color, "total": round(r.total, 2)}
        for r in cat_spending
    ]

    # --- Monthly trend (last 6 months income vs expense) ---
    trend = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        inc = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == "income",
            extract("month", Transaction.date) == m,
            extract("year",  Transaction.date) == y,
        ).scalar() or 0.0
        exp = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == "expense",
            extract("month", Transaction.date) == m,
            extract("year",  Transaction.date) == y,
        ).scalar() or 0.0
        trend.append({
            "month":    m,
            "year":     y,
            "label":    date(y, m, 1).strftime("%b %Y"),
            "income":   round(inc, 2),
            "expenses": round(exp, 2),
        })

    # --- Budget summary ---
    budget_summary = get_budget_summary(uid, month, year)

    # --- Goals ---
    goals      = Goal.query.filter_by(user_id=uid, is_active=True).all()
    goals_data = [enrich_goal(g) for g in goals]

    # --- Recent transactions ---
    recent = (
        Transaction.query
        .filter(Transaction.account_id.in_(account_ids))
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .limit(8)
        .all()
    )

    # --- Unread alerts ---
    unread_alerts = Alert.query.filter_by(user_id=uid, is_read=False).count()

    return jsonify({
        "month":               month,
        "year":                year,
        "total_income":        total_income,
        "total_expenses":      total_expenses,
        "net":                 net,
        "savings_rate":        savings_rate,
        "total_balance":       total_balance,
        "accounts":            [a.to_dict() for a in accounts],
        "spending_by_category": spending_by_category,
        "monthly_trend":       trend,
        "budget_summary":      budget_summary,
        "goals":               goals_data,
        "recent_transactions": [t.to_dict() for t in recent],
        "unread_alerts":       unread_alerts,
    })
