import os
from pathlib import Path
from uuid import uuid4

test_db = Path(__file__).resolve().parents[1] / f"phase2-tests-{uuid4().hex}.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "phase-two-test-secret-value-should-be-random-123456"
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.database import engine
from app.main import app


@pytest.fixture
def client():
    # This is a dedicated disposable SQLite test database, never the configured user database.
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def register(client: TestClient, email: str = "candidate@example.com") -> dict:
    response = client.post("/api/auth/register", json={"name": "Test Candidate", "email": email, "password": "safe-password-123"})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def registered_user(client: TestClient):
    session = register(client)
    return {"session": session, "headers": {"Authorization": f"Bearer {session['access_token']}"}}


def pytest_sessionfinish(session, exitstatus):
    from app.db.database import engine

    engine.dispose()
    test_db.unlink(missing_ok=True)
