import pytest
from app import app as flask_app


@pytest.fixture
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key",
    })
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
