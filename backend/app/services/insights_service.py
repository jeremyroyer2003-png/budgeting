"""
insights_service.py — Peer spending comparison against typical household benchmarks.

Benchmarks are derived from Statistics Canada household expenditure survey data
(proportional distribution, not absolute amounts).
"""

from datetime import date
from sqlalchemy import extract, func
from ..extensions import db

# ── Category bucket definitions ──────────────────────────────────────────────
# Each bucket maps to a list of lowercase keywords matched against category names.
BUCKETS = {
    "Housing":       (28.0, ["rent", "mortgage", "housing", "home", "maintenance"]),
    "Food & Dining": (18.0, ["food", "groceri", "restaurant", "dining", "cafe", "coffee", "meal", "eat"]),
    "Transport":     (13.0, ["transport", "transit", "gas", "fuel", "car", "uber", "lyft", "parking", "auto", "vehicle"]),
    "Shopping":      (10.0, ["shopping", "clothing", "clothes", "amazon", "retail", "store", "apparel"]),
    "Entertainment": ( 7.0, ["entertainment", "netflix", "spotify", "movie", "game", "recreation", "hobby", "sport"]),
    "Utilities":     ( 7.0, ["utilit", "electric", "hydro", "phone", "internet", "water", "cable"]),
    "Health":        ( 6.0, ["health", "medical", "doctor", "pharmacy", "gym", "fitness", "dental", "optom"]),
    "Travel":        ( 5.0, ["travel", "hotel", "airbnb", "flight", "vacation", "trip", "tourism"]),
    "Education":     ( 3.0, ["education", "tuition", "school", "course", "book", "university", "college"]),
    "Other":         ( 3.0, []),   # catch-all
}

# Approximate median Canadian dual-income household monthly income (post-tax) for
# scaling benchmark dollar amounts — used purely for illustration.
_BENCHMARK_INCOME = 7_000.0


def _bucket_for(category_name: str) -> str:
    lower = (category_name or "").lower()
    for bucket, (_, keywords) in BUCKETS.items():
        if bucket == "Other":
            continue
        if any(kw in lower for kw in keywords):
            return bucket
    return "Other"


def compute_peer_comparison(account_ids: list, months: int = 3) -> dict | None:
    from ..models.transaction import Transaction
    from ..models.category    import Category

    if not account_ids:
        return None

    today = date.today()

    # Build month list for last N months
    month_list = []
    m, y = today.month, today.year
    for _ in range(months):
        month_list.append((m, y))
        m -= 1
        if m == 0:
            m, y = 12, y - 1

    # Spending per category over the period
    rows = (
        db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.account_id.in_(account_ids),
            Transaction.type == "expense",
            db.or_(
                *[
                    db.and_(
                        extract("month", Transaction.date) == mm,
                        extract("year",  Transaction.date) == yy,
                    )
                    for mm, yy in month_list
                ]
            ),
        )
        .group_by(Category.id)
        .all()
    )

    # Bucket the spending
    bucket_totals: dict[str, float] = {b: 0.0 for b in BUCKETS}
    for name, total in rows:
        bucket_totals[_bucket_for(name)] += float(total)

    grand_total = sum(bucket_totals.values())
    if grand_total == 0:
        return None

    monthly_avg = grand_total / months

    # Build category list, sorted by benchmark %
    categories = []
    for bucket, (bench_pct, _) in BUCKETS.items():
        user_total   = bucket_totals[bucket]
        user_monthly = round(user_total / months, 2)
        user_pct     = round(user_total / grand_total * 100, 1) if grand_total else 0.0
        bench_monthly = round(_BENCHMARK_INCOME * bench_pct / 100, 2)

        diff = user_pct - bench_pct
        if diff > 3:
            status = "over"
        elif diff < -3:
            status = "under"
        else:
            status = "on-par"

        categories.append({
            "name":            bucket,
            "user_pct":        user_pct,
            "benchmark_pct":   bench_pct,
            "user_monthly":    user_monthly,
            "benchmark_monthly": bench_monthly,
            "status":          status,
        })

    # Sort: biggest difference first
    categories.sort(key=lambda c: abs(c["user_pct"] - c["benchmark_pct"]), reverse=True)

    # Period label
    last_m, last_y = month_list[-1]
    first_m, first_y = month_list[0]
    period = (
        f"{date(last_y, last_m, 1).strftime('%b %Y')} – "
        f"{date(first_y, first_m, 1).strftime('%b %Y')}"
    )

    return {
        "period":            period,
        "months":            months,
        "user_total_monthly": round(monthly_avg, 2),
        "benchmark_income":  _BENCHMARK_INCOME,
        "categories":        categories,
    }
