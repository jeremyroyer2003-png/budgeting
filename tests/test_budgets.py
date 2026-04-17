from datetime import date


def _get_category_id(client, name="Housing"):
    cats = client.get("/api/categories/").get_json()
    return next(c["id"] for c in cats if c["name"] == name)


def test_create_budget(client):
    category_id = _get_category_id(client)
    today = date.today()
    payload = {
        "category_id": category_id,
        "target_amount": 2000.00,
        "month": today.month,
        "year": today.year,
    }
    resp = client.post("/api/budgets/", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["target_amount"] == 2000.00
    assert data["month"] == today.month


def test_upsert_budget(client):
    """
    First POST for a category/month/year creates (201).
    Second POST for the same key updates (200) and changes the amount.
    Uses Shopping to avoid colliding with test_create_budget's Housing entry.
    """
    category_id = _get_category_id(client, name="Shopping")
    today = date.today()
    first = client.post("/api/budgets/", json={
        "category_id": category_id, "target_amount": 1000.00,
        "month": today.month, "year": today.year,
    })
    assert first.status_code == 201   # create → 201

    resp = client.post("/api/budgets/", json={
        "category_id": category_id, "target_amount": 1500.00,
        "month": today.month, "year": today.year,
    })
    assert resp.status_code == 200    # update → 200
    assert resp.get_json()["target_amount"] == 1500.00


def test_list_budgets(client):
    today = date.today()
    resp = client.get(f"/api/budgets/?month={today.month}&year={today.year}")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_budget_summary(client):
    today = date.today()
    resp = client.get(f"/api/budgets/summary?month={today.month}&year={today.year}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "target_amount" in item
        assert "actual_amount" in item
        assert "over_budget" in item
        assert "pct_used" in item


def test_delete_budget(client):
    category_id = _get_category_id(client, "Shopping")
    today = date.today()
    create = client.post("/api/budgets/", json={
        "category_id": category_id, "target_amount": 200.00,
        "month": today.month, "year": today.year,
    })
    budget_id = create.get_json()["id"]
    resp = client.delete(f"/api/budgets/{budget_id}")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == budget_id
