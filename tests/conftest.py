import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from app import create_app
from app.extensions import db as _db
from app.models import User, Account, Category


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        _seed_base_data()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    yield _db
    # Roll back any uncommitted changes after each test
    _db.session.rollback()


def _seed_base_data():
    user = User(email="test@test.com", name="Test User")
    _db.session.add(user)
    _db.session.flush()

    account = Account(user_id=user.id, name="Test Chequing", type="checking", balance=1000.0)
    _db.session.add(account)
    _db.session.flush()

    for name, cat_type, color in [
        ("Salary",       "income",  "#10B981"),
        ("Food & Dining","expense", "#F59E0B"),
        ("Housing",      "expense", "#6366F1"),
        ("Shopping",     "expense", "#8B5CF6"),
    ]:
        _db.session.add(Category(name=name, type=cat_type, color=color, is_system=True))

    _db.session.commit()
