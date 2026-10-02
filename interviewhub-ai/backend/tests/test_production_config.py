import pytest
from pathlib import PurePosixPath
from pydantic import ValidationError

from app.core.config import Settings


def test_health_and_readiness_are_safe(client, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    from app.api import health as health_api

    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/ready").json() == {"status": "ready"}

    class UnavailableEngine:
        def connect(self):
            raise SQLAlchemyError("private database connection string")

    monkeypatch.setattr(health_api, "engine", UnavailableEngine())
    response = client.get("/api/ready")
    assert response.status_code == 503
    assert "private database connection string" not in response.text
    assert "database" not in response.text.lower()


def test_cors_allows_only_the_configured_origin(client):
    from app.core.config import settings

    allowed = client.options(
        "/api/auth/me",
        headers={
            "Origin": settings.frontend_url,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == settings.frontend_url

    denied = client.options(
        "/api/auth/me",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def prod_settings(**overrides):
    values = {
        "environment": "production",
        "database_url": "mysql+pymysql://interviewhub:db-password@mysql.internal:3306/interviewhub",
        "jwt_secret_key": "a-unique-production-secret-with-at-least-48-characters",
        "frontend_url": "https://interviewhub.example.com",
        "upload_storage_path": "/data/resumes",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_configuration_accepts_https_mysql_and_persistent_path():
    config = prod_settings()
    assert config.frontend_url.startswith("https://")
    assert PurePosixPath(str(config.upload_storage_path).replace("\\", "/")).is_absolute()


@pytest.mark.parametrize("overrides", [
    {"jwt_secret_key": "short"},
    {"frontend_url": "http://interviewhub.example.com"},
    {"frontend_url": "*"},
    {"database_url": "sqlite:///production.sqlite3"},
    {"database_url": "mysql+pymysql://username:password@localhost/interviewhub"},
    {"upload_storage_path": "relative/resumes"},
    {"ai_provider": "openai", "ai_model": "model-without-key"},
    {"ai_provider": "openai", "ai_model": "model", "ai_api_key": "test-key", "ai_base_url": "http://ai.internal/v1"},
])
def test_production_configuration_rejects_unsafe_or_incomplete_values(overrides):
    with pytest.raises(ValidationError):
        prod_settings(**overrides)


def test_mysql_url_is_normalized_to_installed_pymysql_driver():
    config = prod_settings(database_url="mysql://interviewhub:db-password@mysql.internal:3306/interviewhub")
    assert config.database_url.get_secret_value().startswith("mysql+pymysql://")


def test_production_validation_errors_do_not_echo_database_credentials():
    with pytest.raises(ValidationError) as raised:
        prod_settings(database_url="mysql://private-user:super-secret-password@localhost/db")
    assert "super-secret-password" not in str(raised.value)
