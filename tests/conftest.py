import pytest
from app import app as flask_app
from dashboard_app import dashboard_app as dash_app


@pytest.fixture
def app():
    flask_app.config.update({"TESTING": True, "SECRET_KEY": "test-secret-key"})
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def dash_client():
    dash_app.config.update({"TESTING": True, "SECRET_KEY": "test-secret-key"})
    return dash_app.test_client()
