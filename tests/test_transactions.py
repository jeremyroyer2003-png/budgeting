import json
from datetime import date
from app.models import Account, Category


def _get_account_id(client):
    resp = client.get("/api/accounts/")
    return resp.get_json()[0]["id"]


def _get_category_id(client, name="Food & Dining"):
    cats = client.get("/api/categories/").get_json()
    return next(c["id"] for c in cats if c["name"] == name)


def test_list_transactions_empty(client):
    resp = client.get("/api/transactions/")
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_create_transaction(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client)
    payload = {
        "account_id": account_id,
        "category_id": category_id,
        "amount": 55.00,
        "type": "expense",
        "description": "Coffee run",
        "date": date.today().isoformat(),
    }
    resp = client.post("/api/transactions/", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["amount"] == 55.00
    assert data["type"] == "expense"
    assert data["description"] == "Coffee run"


def test_create_income_transaction(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client, "Salary")
    payload = {
        "account_id": account_id,
        "category_id": category_id,
        "amount": 3000.00,
        "type": "income",
        "description": "Monthly salary",
        "date": date.today().isoformat(),
    }
    resp = client.post("/api/transactions/", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["type"] == "income"


def test_get_transaction(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client)
    create = client.post("/api/transactions/", json={
        "account_id": account_id,
        "category_id": category_id,
        "amount": 20.00,
        "type": "expense",
        "date": date.today().isoformat(),
    })
    tx_id = create.get_json()["id"]
    resp = client.get(f"/api/transactions/{tx_id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == tx_id


def test_update_transaction(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client)
    create = client.post("/api/transactions/", json={
        "account_id": account_id,
        "category_id": category_id,
        "amount": 40.00,
        "type": "expense",
        "date": date.today().isoformat(),
    })
    tx_id = create.get_json()["id"]
    resp = client.put(f"/api/transactions/{tx_id}", json={"amount": 45.00, "description": "Updated"})
    assert resp.status_code == 200
    assert resp.get_json()["amount"] == 45.00
    assert resp.get_json()["description"] == "Updated"


def test_delete_transaction(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client)
    create = client.post("/api/transactions/", json={
        "account_id": account_id,
        "category_id": category_id,
        "amount": 15.00,
        "type": "expense",
        "date": date.today().isoformat(),
    })
    tx_id = create.get_json()["id"]
    resp = client.delete(f"/api/transactions/{tx_id}")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == tx_id

    get = client.get(f"/api/transactions/{tx_id}")
    assert get.status_code == 404


def test_filter_transactions_by_type(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client)
    client.post("/api/transactions/", json={
        "account_id": account_id, "category_id": category_id,
        "amount": 10.00, "type": "expense", "date": date.today().isoformat(),
    })
    resp = client.get("/api/transactions/?type=expense")
    assert resp.status_code == 200
    for tx in resp.get_json():
        assert tx["type"] == "expense"


def test_create_transaction_invalid_account(client):
    resp = client.post("/api/transactions/", json={
        "account_id": 99999,
        "amount": 10.00,
        "type": "expense",
        "date": date.today().isoformat(),
    })
    assert resp.status_code == 404


# ── Validation tests ──────────────────────────────────────────────────────────

def test_create_transaction_invalid_type(client):
    account_id = _get_account_id(client)
    resp = client.post("/api/transactions/", json={
        "account_id": account_id,
        "amount": 50.00,
        "type": "debit",          # invalid — must be income or expense
        "date": date.today().isoformat(),
    })
    assert resp.status_code == 400
    body = resp.get_json()
    assert "fields" in body
    assert "type" in body["fields"]


def test_create_transaction_negative_amount(client):
    account_id = _get_account_id(client)
    resp = client.post("/api/transactions/", json={
        "account_id": account_id,
        "amount": -25.00,
        "type": "expense",
        "date": date.today().isoformat(),
    })
    assert resp.status_code == 400
    body = resp.get_json()
    assert "amount" in body["fields"]


def test_create_transaction_zero_amount(client):
    account_id = _get_account_id(client)
    resp = client.post("/api/transactions/", json={
        "account_id": account_id,
        "amount": 0,
        "type": "expense",
        "date": date.today().isoformat(),
    })
    assert resp.status_code == 400
    assert "amount" in resp.get_json()["fields"]


def test_create_transaction_bad_date(client):
    account_id = _get_account_id(client)
    resp = client.post("/api/transactions/", json={
        "account_id": account_id,
        "amount": 10.00,
        "type": "expense",
        "date": "not-a-date",
    })
    assert resp.status_code == 400
    assert "date" in resp.get_json()["fields"]


def test_create_transaction_missing_type(client):
    account_id = _get_account_id(client)
    resp = client.post("/api/transactions/", json={
        "account_id": account_id,
        "amount": 10.00,
        "date": date.today().isoformat(),
        # type omitted
    })
    assert resp.status_code == 400
    assert "type" in resp.get_json()["fields"]


def test_update_transaction_invalid_type(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client)
    create = client.post("/api/transactions/", json={
        "account_id": account_id, "category_id": category_id,
        "amount": 20.00, "type": "expense", "date": date.today().isoformat(),
    })
    tx_id = create.get_json()["id"]
    resp = client.put(f"/api/transactions/{tx_id}", json={"type": "transfer"})
    assert resp.status_code == 400
    assert "type" in resp.get_json()["fields"]


def test_update_transaction_negative_amount(client):
    account_id = _get_account_id(client)
    category_id = _get_category_id(client)
    create = client.post("/api/transactions/", json={
        "account_id": account_id, "category_id": category_id,
        "amount": 20.00, "type": "expense", "date": date.today().isoformat(),
    })
    tx_id = create.get_json()["id"]
    resp = client.put(f"/api/transactions/{tx_id}", json={"amount": -5.00})
    assert resp.status_code == 400
    assert "amount" in resp.get_json()["fields"]


def test_create_transaction_no_body(client):
    # Flask may return 415 (wrong content-type) before our handler runs,
    # or 400 if it reaches our validation. Either is a non-2xx rejection.
    resp = client.post("/api/transactions/", data="not json",
                       content_type="text/plain")
    assert resp.status_code in (400, 415)
