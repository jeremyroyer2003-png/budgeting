"""
Seed script — populates the database with realistic sample data.

Run from the backend/ directory:
    python seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Account, Category, Transaction, Budget, Goal, Alert, RecurringTransaction


CATEGORIES = [
    # Income
    {"name": "Salary",          "type": "income",  "color": "#10B981", "icon": "briefcase",   "is_system": True},
    {"name": "Freelance",       "type": "income",  "color": "#34D399", "icon": "code",        "is_system": True},
    {"name": "Investments",     "type": "income",  "color": "#6EE7B7", "icon": "trending-up", "is_system": True},
    {"name": "Other Income",    "type": "income",  "color": "#A7F3D0", "icon": "plus-circle", "is_system": True},
    # Expenses
    {"name": "Housing",         "type": "expense", "color": "#6366F1", "icon": "home",        "is_system": True},
    {"name": "Food & Dining",   "type": "expense", "color": "#F59E0B", "icon": "utensils",    "is_system": True},
    {"name": "Transportation",  "type": "expense", "color": "#3B82F6", "icon": "car",         "is_system": True},
    {"name": "Entertainment",   "type": "expense", "color": "#EC4899", "icon": "film",        "is_system": True},
    {"name": "Healthcare",      "type": "expense", "color": "#EF4444", "icon": "heart",       "is_system": True},
    {"name": "Shopping",        "type": "expense", "color": "#8B5CF6", "icon": "shopping-bag","is_system": True},
    {"name": "Utilities",       "type": "expense", "color": "#14B8A6", "icon": "zap",         "is_system": True},
    {"name": "Subscriptions",   "type": "expense", "color": "#F97316", "icon": "repeat",      "is_system": True},
    {"name": "Travel",          "type": "expense", "color": "#06B6D4", "icon": "map-pin",     "is_system": True},
    {"name": "Education",       "type": "expense", "color": "#84CC16", "icon": "book",        "is_system": True},
    {"name": "Personal Care",   "type": "expense", "color": "#A855F7", "icon": "smile",       "is_system": True},
    {"name": "Savings Transfer","type": "expense", "color": "#0EA5E9", "icon": "piggy-bank",  "is_system": True},
]


def seed():
    app = create_app()
    with app.app_context():
        # Drop and recreate for a clean slate
        db.drop_all()
        db.create_all()

        # --- User ---
        user = User(email="demo@budgetapp.com", name="Alex Morgan")
        db.session.add(user)
        db.session.flush()

        # --- Categories ---
        cat_map = {}
        for c in CATEGORIES:
            cat = Category(**c)
            db.session.add(cat)
            db.session.flush()
            cat_map[c["name"]] = cat

        # --- Accounts ---
        checking = Account(user_id=user.id, name="Main Chequing", type="checking",
                           balance=0.0, institution="TD Bank", account_number_last4="4291")
        savings  = Account(user_id=user.id, name="High-Interest Savings", type="savings",
                           balance=0.0, institution="TD Bank", account_number_last4="8837")
        invest   = Account(user_id=user.id, name="TFSA Investment", type="investment",
                           balance=0.0, institution="Questrade", account_number_last4="3312")
        db.session.add_all([checking, savings, invest])
        db.session.flush()

        # --- Transactions (last 3 months) ---
        today = date.today()

        def add_tx(account, category_name, amount, tx_type, description, days_ago):
            tx_date = today - timedelta(days=days_ago)
            tx = Transaction(
                account_id=account.id,
                category_id=cat_map[category_name].id,
                amount=amount,
                type=tx_type,
                description=description,
                date=tx_date,
            )
            db.session.add(tx)
            if tx_type == "income":
                account.balance += amount
            else:
                account.balance -= amount

        # --- This month ---
        add_tx(checking, "Salary",         5_800.00, "income",  "Bi-weekly payroll",          2)
        add_tx(checking, "Salary",         5_800.00, "income",  "Bi-weekly payroll",         16)
        add_tx(checking, "Freelance",        950.00, "income",  "Design project invoice",    10)
        add_tx(checking, "Housing",        2_150.00, "expense", "Monthly rent",               1)
        add_tx(checking, "Food & Dining",    310.00, "expense", "Weekly groceries x3",        3)
        add_tx(checking, "Food & Dining",     87.50, "expense", "Restaurants & coffee",       5)
        add_tx(checking, "Transportation",   145.00, "expense", "Gas & transit pass",         7)
        add_tx(checking, "Utilities",        210.00, "expense", "Electricity & internet",     4)
        add_tx(checking, "Subscriptions",     62.00, "expense", "Netflix, Spotify, iCloud",   8)
        add_tx(checking, "Shopping",         235.00, "expense", "Clothes & household",        9)
        add_tx(checking, "Entertainment",    120.00, "expense", "Concert tickets",           11)
        add_tx(savings,  "Savings Transfer", 600.00, "expense", "Monthly savings transfer",   2)
        add_tx(savings,  "Savings Transfer", 600.00, "income",  "Transfer from chequing",     2)
        add_tx(invest,   "Investments",      500.00, "income",  "TFSA contribution",          3)

        # --- Last month ---
        add_tx(checking, "Salary",         5_800.00, "income",  "Bi-weekly payroll",         35)
        add_tx(checking, "Salary",         5_800.00, "income",  "Bi-weekly payroll",         49)
        add_tx(checking, "Housing",        2_150.00, "expense", "Monthly rent",              32)
        add_tx(checking, "Food & Dining",    420.00, "expense", "Groceries x4",              34)
        add_tx(checking, "Food & Dining",    155.00, "expense", "Restaurants",               38)
        add_tx(checking, "Transportation",   130.00, "expense", "Gas",                       40)
        add_tx(checking, "Utilities",        195.00, "expense", "Electricity & internet",    33)
        add_tx(checking, "Subscriptions",     62.00, "expense", "Subscriptions",             36)
        add_tx(checking, "Healthcare",       180.00, "expense", "Dental appointment",        42)
        add_tx(checking, "Shopping",         410.00, "expense", "Electronics — over budget", 45)
        add_tx(checking, "Travel",           650.00, "expense", "Weekend trip",              50)
        add_tx(savings,  "Savings Transfer", 600.00, "expense", "Monthly savings transfer",  32)
        add_tx(savings,  "Savings Transfer", 600.00, "income",  "Transfer from chequing",    32)
        add_tx(invest,   "Investments",      500.00, "income",  "TFSA contribution",         33)

        # --- Two months ago ---
        add_tx(checking, "Salary",         5_800.00, "income",  "Bi-weekly payroll",         63)
        add_tx(checking, "Salary",         5_800.00, "income",  "Bi-weekly payroll",         77)
        add_tx(checking, "Freelance",        700.00, "income",  "Consulting invoice",        70)
        add_tx(checking, "Housing",        2_150.00, "expense", "Monthly rent",              62)
        add_tx(checking, "Food & Dining",    380.00, "expense", "Groceries",                 64)
        add_tx(checking, "Transportation",   160.00, "expense", "Gas & car maintenance",     65)
        add_tx(checking, "Utilities",        220.00, "expense", "Electricity & internet",    63)
        add_tx(checking, "Subscriptions",     62.00, "expense", "Subscriptions",             66)
        add_tx(checking, "Education",        299.00, "expense", "Online course",             72)
        add_tx(checking, "Personal Care",     95.00, "expense", "Haircut & gym",             68)
        add_tx(savings,  "Savings Transfer", 600.00, "expense", "Monthly savings transfer",  62)
        add_tx(savings,  "Savings Transfer", 600.00, "income",  "Transfer from chequing",    62)
        add_tx(invest,   "Investments",      500.00, "income",  "TFSA contribution",         63)

        db.session.flush()

        # --- Recurring transactions ---
        rec1 = RecurringTransaction(
            account_id=checking.id,
            category_id=cat_map["Housing"].id,
            amount=2_150.00,
            type="expense",
            description="Monthly rent",
            frequency="monthly",
            start_date=date(today.year, today.month, 1),
            next_date=date(today.year, today.month, 1) + timedelta(days=30),
        )
        rec2 = RecurringTransaction(
            account_id=checking.id,
            category_id=cat_map["Subscriptions"].id,
            amount=62.00,
            type="expense",
            description="Netflix, Spotify, iCloud",
            frequency="monthly",
            start_date=date(today.year, today.month, 8),
            next_date=date(today.year, today.month, 8) + timedelta(days=30),
        )
        rec3 = RecurringTransaction(
            account_id=checking.id,
            category_id=cat_map["Salary"].id,
            amount=5_800.00,
            type="income",
            description="Bi-weekly payroll",
            frequency="biweekly",
            start_date=date(today.year, today.month, 1),
            next_date=today + timedelta(days=14),
        )
        db.session.add_all([rec1, rec2, rec3])
        db.session.flush()

        # --- Budgets (current month) ---
        month, year = today.month, today.year
        budget_targets = {
            "Housing":        2_150.00,
            "Food & Dining":    500.00,
            "Transportation":   200.00,
            "Entertainment":    150.00,
            "Shopping":         300.00,
            "Utilities":        250.00,
            "Subscriptions":     80.00,
            "Healthcare":       100.00,
            "Personal Care":     80.00,
            "Travel":           200.00,
            "Education":        150.00,
            "Savings Transfer": 600.00,
        }
        for cat_name, target in budget_targets.items():
            b = Budget(
                user_id=user.id,
                category_id=cat_map[cat_name].id,
                month=month,
                year=year,
                target_amount=target,
            )
            db.session.add(b)

        # --- Goals ---
        goals = [
            Goal(
                user_id=user.id,
                name="Emergency Fund",
                type="savings",
                target_amount=15_000.00,
                current_amount=savings.balance,
                monthly_target=600.00,
                target_date=date(today.year + 1, today.month, 1),
                notes="3 months of living expenses",
            ),
            Goal(
                user_id=user.id,
                name="TFSA Max Contribution",
                type="investment",
                target_amount=7_000.00,
                current_amount=invest.balance,
                monthly_target=500.00,
                target_date=date(today.year, 12, 31),
                notes="Max out annual TFSA room",
            ),
            Goal(
                user_id=user.id,
                name="House Down Payment",
                type="savings",
                target_amount=80_000.00,
                current_amount=8_000.00,
                monthly_target=1_200.00,
                target_date=date(today.year + 5, today.month, 1),
                notes="20% down on a $400K property",
            ),
            Goal(
                user_id=user.id,
                name="Vacation Fund",
                type="purchase",
                target_amount=3_500.00,
                current_amount=850.00,
                monthly_target=350.00,
                target_date=date(today.year, 12, 1),
                notes="Europe trip in December",
            ),
        ]
        db.session.add_all(goals)
        db.session.flush()

        # --- Initial alerts ---
        alerts = [
            Alert(
                user_id=user.id,
                type="overspending",
                severity="critical",
                message="You exceeded your Shopping budget last month by $110.00.",
                is_read=False,
            ),
            Alert(
                user_id=user.id,
                type="goal_at_risk",
                severity="warning",
                message="House Down Payment goal is behind schedule. Consider increasing your monthly contribution.",
                is_read=False,
            ),
            Alert(
                user_id=user.id,
                type="info",
                severity="info",
                message="You're on track with your Emergency Fund goal. Keep it up!",
                is_read=True,
            ),
        ]
        db.session.add_all(alerts)
        db.session.commit()

        print("✓ Database seeded successfully.")
        print(f"  User:         {user.name} ({user.email})")
        print(f"  Accounts:     {checking.name}, {savings.name}, {invest.name}")
        print(f"  Categories:   {len(CATEGORIES)}")
        print(f"  Transactions: {Transaction.query.count()}")
        print(f"  Budgets:      {Budget.query.count()}")
        print(f"  Goals:        {Goal.query.count()}")
        print(f"  Alerts:       {Alert.query.count()}")


if __name__ == "__main__":
    seed()
