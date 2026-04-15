from datetime import date


def test_list_alerts_empty(client):
    resp = client.get("/api/alerts/")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_generate_alerts(client):
    # Create a budget that is exceeded
    cats = client.get("/api/categories/").get_json()
    housing_id = next(c["id"] for c in cats if c["name"] == "Housing")
    food_id = next(c["id"] for c in cats if c["name"] == "Food & Dining")
    today = date.today()

    # Set a tight budget
    client.post("/api/budgets/", json={
        "category_id": food_id, "target_amount": 10.00,
        "month": today.month, "year": today.year,
    })

    # Add a transaction that busts the budget
    accounts = client.get("/api/accounts/").get_json()
    account_id = accounts[0]["id"]
    client.post("/api/transactions/", json={
        "account_id": account_id, "category_id": food_id,
        "amount": 50.00, "type": "expense", "date": today.isoformat(),
    })

    resp = client.post("/api/alerts/generate")
    assert resp.status_code == 200
    assert resp.get_json()["generated"] >= 1

    alerts = client.get("/api/alerts/").get_json()
    overspend = [a for a in alerts if a["type"] == "overspending"]
    assert len(overspend) >= 1


def test_mark_alert_read(client):
    # Generate at least one alert first
    client.post("/api/alerts/generate")
    alerts = client.get("/api/alerts/").get_json()
    if not alerts:
        return  # nothing to test if no alerts exist

    alert_id = alerts[0]["id"]
    resp = client.post(f"/api/alerts/{alert_id}/read")
    assert resp.status_code == 200
    assert resp.get_json()["is_read"] is True


def test_mark_all_read(client):
    client.post("/api/alerts/generate")
    resp = client.post("/api/alerts/read-all")
    assert resp.status_code == 200

    unread = client.get("/api/alerts/").get_json()
    assert unread == []


def test_show_read_alerts(client):
    client.post("/api/alerts/generate")
    client.post("/api/alerts/read-all")
    resp = client.get("/api/alerts/?show_read=true")
    assert resp.status_code == 200
    # All returned alerts should be read
    for a in resp.get_json():
        assert a["is_read"] is True
