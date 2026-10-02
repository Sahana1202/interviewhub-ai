from fastapi.testclient import TestClient

from app.db.migrations import ensure_onboarding_completed_column
from sqlalchemy import create_engine, inspect, text
from pathlib import Path
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings
from app.core.security import hash_password, verify_password


def register(client: TestClient, email: str) -> dict:
    response = client.post("/api/auth/register", json={"name": "Test Candidate", "email": email, "password": "safe-password-123"})
    assert response.status_code == 201
    return response.json()


def test_registration_validation_and_safe_response(client: TestClient):
    payload = {"name": "Test Candidate", "email": "new@example.com", "password": "safe-password-123"}
    created = client.post("/api/auth/register", json=payload)
    assert created.status_code == 201
    assert "password_hash" not in created.text
    assert created.json()["user"]["profile"]["onboarding_completed"] is False

    duplicate = client.post("/api/auth/register", json=payload)
    assert duplicate.status_code == 409
    assert client.post("/api/auth/register", json={**payload, "email": "not-an-email"}).status_code == 422
    weak = client.post("/api/auth/register", json={**payload, "email": "short@example.com", "password": "secret"})
    assert weak.status_code == 422
    assert "secret" not in weak.text


def test_login_accepts_valid_and_rejects_invalid_credentials(client: TestClient):
    payload = {"name": "Login Candidate", "email": "login@example.com", "password": "safe-password-123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]}).status_code == 200
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": "incorrect-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "missing@example.com", "password": payload["password"]}).status_code == 401


def test_password_hashing_and_bearer_token_failures_are_safe(client):
    encoded = hash_password("long-enough-safe-password")
    assert encoded != "long-enough-safe-password"
    assert verify_password("long-enough-safe-password", encoded)
    assert not verify_password("incorrect-password", encoded)
    expired = jwt.encode({"sub":"1","exp":datetime.now(timezone.utc)-timedelta(minutes=1)}, settings.jwt_secret_key.get_secret_value(), algorithm="HS256")
    for token in ("malformed", expired, "eyJhbGciOiJub25lIn0.eyJzdWIiOiIxIn0."):
        response=client.get("/api/auth/me",headers={"Authorization":f"Bearer {token}"})
        assert response.status_code==401
        assert "secret" not in response.text.lower()


def test_profile_is_private_and_updates_authenticated_users_profile(client: TestClient, registered_user):
    headers = registered_user["headers"]
    initial = client.get("/api/profile", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["college"] is None
    assert client.get("/api/profile").status_code == 401
    assert client.put("/api/profile", json={"college": "Example College"}).status_code == 401

    updated = client.put("/api/profile", headers=headers, json={
        "college": "Example College", "degree": "B.E.", "department": "Computer Science",
        "graduation_year": 2027, "experience_level": "Fresher", "target_role": "Backend Developer",
        "target_industry": "Software", "location": "Tamil Nadu",
    })
    assert updated.status_code == 200
    assert updated.json()["target_role"] == "Backend Developer"
    assert updated.json()["onboarding_completed"] is False

    # The API does not accept a client-supplied identity field.
    assert client.put("/api/profile", headers=headers, json={"user_id": 999}).status_code == 422
    assert client.put("/api/profile", headers=headers, json={"graduation_year": 1800}).status_code == 422


def test_onboarding_validation_completion_and_idempotency(client: TestClient, registered_user):
    headers = registered_user["headers"]
    assert client.post("/api/profile/onboarding", json={"experience_level": "Fresher", "target_role": "Developer"}).status_code == 401
    incomplete = client.post("/api/profile/onboarding", headers=headers, json={"college": "Example College"})
    assert incomplete.status_code == 422
    invalid_year = client.post("/api/profile/onboarding", headers=headers, json={
        "experience_level": "Student", "target_role": "Developer", "graduation_year": 1900,
    })
    assert invalid_year.status_code == 422

    payload = {"college": "Example College", "degree": "B.E.", "department": "CSE", "graduation_year": 2027,
               "experience_level": "Student", "target_role": "Full Stack Developer", "target_industry": "Software", "location": "Tamil Nadu"}
    completed = client.post("/api/profile/onboarding", headers=headers, json=payload)
    assert completed.status_code == 200
    assert completed.json()["onboarding_completed"] is True
    repeated = client.post("/api/profile/onboarding", headers=headers, json=payload)
    assert repeated.status_code == 200
    assert repeated.json()["onboarding_completed"] is True
    cleared = client.put("/api/profile", headers=headers, json={"target_role": None})
    assert cleared.status_code == 200
    assert cleared.json()["onboarding_completed"] is False


def test_profile_routes_never_target_another_user(client: TestClient):
    first = register(client, "first@example.com")
    second = register(client, "second@example.com")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    client.put("/api/profile", headers=first_headers, json={"target_role": "First User Role"})
    first_profile = client.get("/api/profile", headers=first_headers).json()
    second_profile = client.get("/api/profile", headers=second_headers).json()
    assert first_profile["target_role"] == "First User Role"
    assert second_profile["target_role"] is None


def test_development_migration_adds_column_without_recreating_table():
    db_path = Path(__file__).resolve().parents[1] / "phase2-migration-test.sqlite3"
    db_path.unlink(missing_ok=True)
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE user_profiles (id INTEGER PRIMARY KEY, college VARCHAR(200))"))
        connection.execute(text("INSERT INTO user_profiles (id, college) VALUES (1, 'Preserved College')"))
    ensure_onboarding_completed_column(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("user_profiles")}
    with engine.connect() as connection:
        row = connection.execute(text("SELECT college, onboarding_completed FROM user_profiles WHERE id=1")).one()
    assert "onboarding_completed" in columns
    assert row[0] == "Preserved College"
    assert row[1] in (0, False)
    engine.dispose()
    db_path.unlink(missing_ok=True)
