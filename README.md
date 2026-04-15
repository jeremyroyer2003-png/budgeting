# ClearBudget

A serious personal finance app that compares what you *planned* to do financially versus what you *actually* did — helping you understand spending patterns, track savings and investment goals, and stay ahead of budget overruns.

---

## Product Vision

Most people know what they *should* do with money. Few can clearly see the gap between intention and action.

ClearBudget surfaces that gap by:

- Tracking every transaction against a monthly budget plan
- Measuring goal progress (savings, investment, debt payoff, purchases)
- Generating automated alerts when spending is too high or savings are behind target
- Showing side-by-side comparisons: "What did I want to do?" vs "What did I actually do?"

---

## Stack & Why

| Layer | Technology | Reason |
|---|---|---|
| Backend | Python 3.11 + Flask | Lightweight, widely understood, easy to extend |
| Database | SQLite + SQLAlchemy ORM | Zero config locally; swap to PostgreSQL for production with one env var change |
| Frontend | Vanilla HTML/CSS/JS | No build step, easy to understand, fast to iterate |
| Charts | Chart.js (CDN) | Excellent charts with minimal setup |
| Icons | Feather Icons (CDN) | Clean, consistent icon set |

---

## Folder Structure

```
budgeting/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── config.py            # Config classes (default, testing)
│   │   ├── extensions.py        # SQLAlchemy + CORS init
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── category.py
│   │   │   ├── transaction.py
│   │   │   ├── recurring_transaction.py
│   │   │   ├── budget.py
│   │   │   ├── goal.py
│   │   │   └── alert.py
│   │   ├── routes/              # Blueprint-based REST API
│   │   │   ├── transactions.py
│   │   │   ├── categories.py
│   │   │   ├── budgets.py
│   │   │   ├── goals.py
│   │   │   ├── alerts.py
│   │   │   ├── accounts.py
│   │   │   ├── dashboard.py
│   │   │   └── recurring.py
│   │   ├── services/            # Business logic
│   │   │   ├── alert_service.py
│   │   │   ├── budget_service.py
│   │   │   └── goal_service.py
│   │   └── integrations/        # Bank sync extension point
│   │       ├── base_provider.py  # Abstract interface
│   │       ├── mock_provider.py  # Demo data provider
│   │       ├── plaid_provider.py # (stub — add credentials to enable)
│   │       └── flinks_provider.py# (stub — add credentials to enable)
│   ├── seed.py                  # Sample data seeder
│   ├── run.py                   # Entry point
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Single-page app shell
│   ├── css/
│   │   └── style.css            # Full design system
│   └── js/
│       ├── api.js               # REST API wrapper
│       ├── app.js               # SPA router, modals, shared state
│       ├── dashboard.js         # Dashboard page
│       ├── transactions.js      # Transactions CRUD
│       ├── budgets.js           # Budget management
│       ├── goals.js             # Financial goals
│       └── alerts.js            # Alerts and dismissals
├── tests/
│   ├── conftest.py              # Pytest fixtures (in-memory DB)
│   ├── test_transactions.py
│   ├── test_budgets.py
│   ├── test_goals.py
│   └── test_alerts.py
└── README.md
```

---

## Setup & Running

### 1. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Seed the database with sample data

```bash
cd backend
python seed.py
```

This creates `backend/budgeting.db` with a demo user, accounts, 3 months of transactions, budgets, goals, and alerts.

### 3. Start the backend

```bash
cd backend
python run.py
```

The API is now live at `http://localhost:5000`.

### 4. Open the frontend

Open `frontend/index.html` directly in your browser — no build step required.

> **Tip:** For the best experience (and to avoid CORS issues), serve the frontend over HTTP:
> ```bash
> cd frontend
> python3 -m http.server 3000
> ```
> Then visit `http://localhost:3000`.

---

## API Reference

Base URL: `http://localhost:5000/api`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/transactions/` | List transactions (filters: type, category_id, month, year, limit) |
| POST   | `/transactions/` | Create transaction |
| GET    | `/transactions/:id` | Get single transaction |
| PUT    | `/transactions/:id` | Update transaction |
| DELETE | `/transactions/:id` | Delete transaction |
| GET    | `/categories/` | List all categories |
| POST   | `/categories/` | Create category |
| GET    | `/accounts/` | List accounts |
| POST   | `/accounts/` | Create account |
| GET    | `/budgets/` | List budgets (filter: month, year) |
| POST   | `/budgets/` | Set/update a budget target (upserts) |
| DELETE | `/budgets/:id` | Delete budget |
| GET    | `/budgets/summary` | Budget targets vs actuals with over-budget flags |
| GET    | `/goals/` | List active goals |
| POST   | `/goals/` | Create goal |
| PUT    | `/goals/:id` | Update goal |
| DELETE | `/goals/:id` | Archive goal |
| GET    | `/alerts/` | List alerts (filter: show_read) |
| POST   | `/alerts/:id/read` | Mark alert as read |
| POST   | `/alerts/read-all` | Dismiss all unread alerts |
| POST   | `/alerts/generate` | Trigger alert generation |
| GET    | `/dashboard/` | Full dashboard summary (filter: month, year) |
| GET    | `/recurring/` | List recurring transaction rules |
| POST   | `/recurring/` | Create recurring rule |
| PUT    | `/recurring/:id` | Update recurring rule |
| DELETE | `/recurring/:id` | Disable recurring rule |

---

## Running Tests

```bash
cd budgeting   # project root
pip install -r backend/requirements.txt
pytest tests/ -v
```

Tests use an in-memory SQLite database seeded with base data. No external services needed.

---

## Current Features

- **Dashboard** — Monthly income, expenses, net, savings rate, 6-month trend chart, spending by category donut chart, budget health, goal progress, account balances, recent transactions
- **Transactions** — Full CRUD, filter by type/category/month, balance auto-updates on account
- **Budgets** — Monthly targets per category, actual vs target with progress bars, over-budget warnings
- **Goals** — Savings, investment, debt payoff, purchase goals with progress tracking and on-track detection
- **Alerts** — Auto-generated alerts for overspending and off-track goals, severity levels (info/warning/critical)
- **Recurring Transactions** — Rules for regular income/expenses (rent, salary, subscriptions)
- **Accounts** — Multiple account types (checking, savings, investment, credit)
- **Categories** — Income and expense categories with color coding
- **Sample Data** — 3 months of realistic transactions, budgets, goals, and alerts via `seed.py`
- **Bank Integration Layer** — Abstract provider interface ready for Plaid/Flinks

---

## Future Roadmap

### Phase 2 — Real Bank Sync

See [Bank Integration](#bank-account-integration) section below.

### Phase 3 — Multi-User & Authentication

1. Replace the `DEFAULT_USER_ID = 1` constant in each route with `current_user.id` from Flask-Login or a JWT middleware
2. Add `User` registration and login endpoints
3. Add password hashing (bcrypt)
4. All existing models already have `user_id` foreign keys — no schema changes needed

### Phase 4 — Production Deployment

1. Replace SQLite with PostgreSQL: change `DATABASE_URL` env var
2. Deploy Flask behind Gunicorn + Nginx
3. Use Flask-Migrate (Alembic) for schema migrations
4. Add environment-based config for secrets
5. Containerize with Docker Compose (api + db + frontend)

### Phase 5 — Notifications & Reminders

1. Add a scheduled job (APScheduler or Celery) to run `generate_alerts()` daily
2. Email or push notifications when critical alerts are triggered
3. Weekly summary digest

### Phase 6 — Investment Tracking

1. Connect investment accounts via Plaid or Questrade API
2. Track portfolio value over time
3. Compare actual investment contributions to targets

### Phase 7 — API Documentation

1. Add Flask-RESTX or Flasgger for auto-generated Swagger/OpenAPI docs
2. Expose docs at `/api/docs`

---

## Bank Account Integration

The app is designed so that bank/credit-card syncing can be added without rewriting business logic.

### How it works today

`backend/app/integrations/base_provider.py` defines an abstract interface:

```python
class BaseProvider(ABC):
    def authenticate(self, credentials: dict) -> None: ...
    def get_accounts(self, user_token: str) -> list[RemoteAccount]: ...
    def get_transactions(self, user_token, account_id, start_date, end_date) -> list[RemoteTransaction]: ...
```

`MockProvider` implements this with realistic fake data for demos and tests.

### Adding Plaid

1. Sign up at [plaid.com](https://plaid.com) and obtain `client_id`, `secret`, and `access_token`
2. `pip install plaid-python`
3. Create `backend/app/integrations/plaid_provider.py` implementing `BaseProvider`
4. Add an API endpoint like `POST /api/accounts/sync` that:
   - Calls `PlaidProvider().get_transactions(user_token, account_id, start, end)`
   - Maps `RemoteTransaction` fields to the `Transaction` model
   - Deduplicates by `provider_transaction_id` (already a field on `Account`)
5. Register it in `integrations/__init__.py`

### Adding Flinks

Same pattern — implement `BaseProvider` using the Flinks REST API. Flinks uses a login ID + request ID flow instead of OAuth, but the abstract interface hides that detail.

### Data model for sync

The `Account` model already carries:
- `is_connected: bool`
- `provider: str` (e.g. "plaid", "flinks")
- `provider_account_id: str`

Transactions carry:
- `recurring_transaction_id` for linking generated entries to rules

---

## Data Model

```
User
 └── Account (checking / savings / investment / credit)
      └── Transaction (income / expense, linked to Category)
      └── RecurringTransaction (daily / weekly / monthly / yearly rules)

User
 └── Budget (target amount per Category per month)
 └── Goal (savings / investment / debt_payoff / purchase)
 └── Alert (overspending / goal_at_risk / savings_behind / info)

Category (shared; income or expense type; system + user-defined)
```

---

## Development Notes

- `DEFAULT_USER_ID = 1` is used throughout routes to scope data to the seeded demo user. This is the only change needed when adding authentication.
- The app uses SQLAlchemy sessions — do not mix raw SQL with ORM calls.
- Alert generation is idempotent: re-running `POST /api/alerts/generate` will not duplicate existing unread alerts of the same type/category.
- Budget upsert: `POST /api/budgets/` creates or updates — no separate PUT needed for budgets.
