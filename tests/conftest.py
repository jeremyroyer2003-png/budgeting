import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
from flask.testing import FlaskClient
from flask_jwt_extended import create_access_token

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


class AuthClient:
    """Wraps FlaskClient and injects a JWT Authorization header automatically."""

    def __init__(self, flask_client: FlaskClient, token: str):
        self._client = flask_client
        self._auth  = {"Authorization": f"Bearer {token}"}

    def _merge(self, kwargs):
        headers = {**self._auth, **kwargs.pop("headers", {})}
        return {**kwargs, "headers": headers}

    def get(self, *a, **kw):     return self._client.get(*a, **self._merge(kw))
    def post(self, *a, **kw):    return self._client.post(*a, **self._merge(kw))
    def put(self, *a, **kw):     return self._client.put(*a, **self._merge(kw))
    def delete(self, *a, **kw):  return self._client.delete(*a, **self._merge(kw))
    def patch(self, *a, **kw):   return self._client.patch(*a, **self._merge(kw))


@pytest.fixture
def client(app):
    """Authenticated test client — all requests carry a valid JWT."""
    with app.app_context():
        user = User.query.filter_by(email="test@test.com").first()
        token = create_access_token(identity=str(user.id))
    return AuthClient(app.test_client(), token)


@pytest.fixture
def raw_client(app):
    """Unauthenticated test client — for testing auth endpoints themselves."""
    return app.test_client()


@pytest.fixture
def db(app):
    yield _db
    _db.session.rollback()


def _seed_base_data():
    user = User(email="test@test.com", name="Test User")
    user.set_password("testpassword123")
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
