from datetime import date, timedelta


def test_create_goal(client):
    payload = {
        "name": "Emergency Fund",
        "type": "savings",
        "target_amount": 10000.00,
        "current_amount": 2500.00,
        "monthly_target": 500.00,
        "target_date": (date.today() + timedelta(days=365)).isoformat(),
    }
    resp = client.post("/api/goals/", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Emergency Fund"
    assert data["target_amount"] == 10000.00
    assert data["progress_pct"] == 25.0


def test_list_goals(client):
    client.post("/api/goals/", json={
        "name": "Vacation Fund",
        "type": "purchase",
        "target_amount": 3000.00,
        "current_amount": 300.00,
    })
    resp = client.get("/api/goals/")
    assert resp.status_code == 200
    assert len(resp.get_json()) >= 1


def test_update_goal(client):
    create = client.post("/api/goals/", json={
        "name": "Car Fund",
        "type": "purchase",
        "target_amount": 5000.00,
    })
    goal_id = create.get_json()["id"]
    resp = client.put(f"/api/goals/{goal_id}", json={"current_amount": 1000.00})
    assert resp.status_code == 200
    assert resp.get_json()["current_amount"] == 1000.00
    assert resp.get_json()["progress_pct"] == 20.0


def test_delete_goal_soft(client):
    """Delete (soft) should hide the goal from the list."""
    create = client.post("/api/goals/", json={
        "name": "Temp Goal",
        "type": "savings",
        "target_amount": 100.00,
    })
    goal_id = create.get_json()["id"]
    resp = client.delete(f"/api/goals/{goal_id}")
    assert resp.status_code == 200

    goals = client.get("/api/goals/").get_json()
    assert not any(g["id"] == goal_id for g in goals)


def test_goal_on_track_enrichment(client):
    """Goals with a target_date and monthly_target should include on_track status."""
    future = (date.today() + timedelta(days=730)).isoformat()
    create = client.post("/api/goals/", json={
        "name": "Investment Goal",
        "type": "investment",
        "target_amount": 12000.00,
        "current_amount": 0.00,
        "monthly_target": 600.00,
        "target_date": future,
    })
    data = create.get_json()
    assert "on_track" in data
    assert data["on_track"] is not None


def test_goal_progress_pct_caps_at_100(client):
    create = client.post("/api/goals/", json={
        "name": "Completed Goal",
        "type": "savings",
        "target_amount": 500.00,
        "current_amount": 600.00,
    })
    data = create.get_json()
    assert data["progress_pct"] == 100.0
