# ClearBudget — Project Context for Claude Code

## What is this project?

ClearBudget is a personal finance web app built for francophone Canadian users.
The goal is to help people understand their spending, stick to budgets, and reach
life goals — with UX designed around behavioral economics (habit loops, forward-looking
language, Kakeibo reflection, goal-gradient effect).

## Tech stack

- **Backend**: Python / Flask, SQLAlchemy ORM, SQLite (dev), Flask-JWT-Extended for auth
- **Frontend**: Vanilla JS, HTML/CSS — no framework, Chart.js for charts, Feather icons
- **Tests**: pytest (32 tests, all passing) — run with `pytest tests/` from project root
- **Branch**: `claude/plan-budgeting-app-mSdcq`

## How to run locally

```bash
# Backend (from project root)
cd backend
pip install -r requirements.txt
python run.py          # runs on http://127.0.0.1:5000

# Seed demo data (first time only)
python seed.py         # creates demo@clearbudget.app / demo1234

# Frontend
# Right-click frontend/index.html → "Open with Live Server" in VS Code
```

## Project structure

```
backend/
  app/
    models/         — User, Account, Transaction, Category, Budget, Goal,
                      Alert, RecurringTransaction, Household, HouseholdMember
    routes/         — auth, accounts, transactions, budgets, goals, alerts,
                      dashboard, subscriptions, household, plaid
    services/       — budget_service, goal_service, alert_service,
                      health_score_service, weekly_summary_service,
                      subscription_service, insights_service
    utils/          — auth.py (current_user_id helper)
    extensions.py   — db, jwt, cors
  run.py
  seed.py
frontend/
  index.html        — single-page app, all pages as <section> tags
  css/style.css     — full design system with dark mode ([data-theme="dark"])
  js/
    app.js          — routing, nav, dark mode toggle, SW registration
    api.js          — all fetch() calls to Flask backend
    dashboard.js    — main dashboard render
    transactions.js — transaction list + add/edit modal
    budgets.js      — budget cards with per-day remaining
    goals.js        — goal cards with time-to-goal headline
    alerts.js       — alerts list + weekly digest with challenge block
    subscriptions.js
    insights.js     — peer comparison (Stats Canada benchmarks)
    family.js       — household / family mode
    auth.js
  manifest.json     — PWA manifest
  sw.js             — service worker (cache-first static, network-first API)
  icons/            — SVG icons for PWA
tests/
  test_alerts.py, test_budgets.py, test_goals.py, test_transactions.py
```

## Key features built

### Dashboard
- 4 summary stat cards (income, expenses, net, savings rate)
- **Financial Runway** — days of expenses covered by current balance
- **Savings Streak** — consecutive months where expenses < income
- **Daily Insight** — one smart sentence (5-priority logic: over budget →
  good savings rate → goal near completion → positive net → top category)
- Financial Health Score (0-100) with 4 components, each with a tip
- Month-end projection with subscription detection
- 6-month income vs expenses trend chart
- Spending by category doughnut chart
- Budget health mini-bars, goal progress mini-bars
- Recent transactions

### Budgets page
- Per-day remaining shown for current month ("$12.50/day for 8 more days")
- Over-budget: recovery rate shown ("spend $X/day less to close the gap")
- Surplus reframed positively ("Finished $X under budget — great discipline!")

### Goals page
- **Time-to-goal as headline** ("On track for August 2026 · 16 months away")
- Ghost bar shows expected pace vs actual progress
- Actionable gap callout when behind ("Add $85/month to get back on track")
- Velocity insight based on last 30 days of savings activity

### Alerts page
- Forward-looking, actionable alert messages (not guilt-based)
- All messages include days remaining + per-day recovery amounts
- Weekly digest with: spent, income, net, tx count, top categories,
  daily bar chart, and **This Week's Challenge** (context-aware)

### Transactions
- **Kakeibo reflection picker** — when adding an expense, user selects:
  Need / Want / Culture / Unexpected (creates mindful spending moment)

### Other features
- Dark mode (CSS custom properties, `[data-theme="dark"]`, toggle in sidebar)
- PWA (installable, service worker, offline cache)
- Peer comparison (spending vs Stats Canada benchmarks by category)
- Family/household mode (invite members, shared overview)
- Subscription detection (recurring transaction pattern recognition)
- Plaid integration scaffold (sandbox ready)

## UX philosophy

All UX decisions are grounded in behavioral economics research:
- **Forward-looking language**: "You have $X left" not "You spent $Y"
- **Specific + actionable**: always include a concrete number to act on
- **Habit loops**: streak counter, weekly challenge, daily insight
- **Goal-gradient effect**: time-to-goal framing pulls users forward
- **Kakeibo**: intentional spending reflection at point of entry
- **Aha moment within 60 seconds**: daily insight card is the first thing seen

## Alert message logic (alert_service.py)

- Over budget: calculates `days_remaining` and shows `$/day` recovery rate
- At 80%: shows `$/day` budget remaining
- Goal at risk: shows exact monthly shortfall
- No monthly target: suggests amount based on 24-month horizon

## Health score components (health_score_service.py)

Each component returns `(score, detail, tip)`:
1. **Savings Rate** (25pts) — 3-month rolling average, full marks at ≥20%
2. **Budget Adherence** (25pts) — fraction of budgets on or under limit
3. **Goal Progress** (25pts) — actual vs ghost pace per goal
4. **Spending Trend** (25pts) — current month daily rate vs previous month

## Dashboard backend fields (dashboard.py)

`GET /api/dashboard/?month=M&year=Y` returns:
- `total_income`, `total_expenses`, `net`, `savings_rate`
- `total_balance`, `accounts`
- `spending_by_category`, `monthly_trend`
- `budget_summary`, `goals`, `recent_transactions`
- `projection` (current month only — includes subscription detection)
- `health_score` (full score object with components + tips)
- `buffer_days` (total_balance / avg_daily_expense_last_30d)
- `savings_streak` (consecutive months expenses < income, up to 12)
- `daily_insight` (one interpreted sentence)
- `unread_alerts`

## Weekly summary (weekly_summary_service.py)

`GET /api/alerts/weekly-summary` returns:
- `week_start/end/label`, `total_income`, `total_expense`, `net`
- `prev_expense`, `wow_pct` (week-over-week % change)
- `tx_count`, `top_categories` (top 5), `daily` (Mon–Sun breakdown)
- `challenge` (context-aware actionable goal for coming week)

## Demo credentials

- Email: `demo@clearbudget.app`
- Password: `demo1234`

## Git workflow

- Always develop on branch: `claude/plan-budgeting-app-mSdcq`
- Push with: `git push -u origin claude/plan-budgeting-app-mSdcq`
- User syncs locally with: `git pull` in VS Code terminal
- Run tests before pushing: `pytest tests/`
