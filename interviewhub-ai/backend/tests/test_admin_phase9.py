from sqlalchemy import select
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from app.db.database import SessionLocal
from app.models.user import User


def make_admin(session):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == session["user"]["id"]))
        user.role = "admin"
        db.commit()
    return {"Authorization": f"Bearer {session['access_token']}"}


def test_admin_api_requires_auth_and_denies_candidates(client, registered_user):
    assert client.get("/api/admin/dashboard").status_code == 401
    assert client.get("/api/admin/dashboard", headers=registered_user["headers"]).status_code == 403


def test_admin_dashboard_and_user_controls_are_audited(client):
    admin_session = client.post("/api/auth/register", json={"name":"Admin", "email":"admin@test.example", "password":"safe-password-123"}).json()
    admin_headers = make_admin(admin_session)
    candidate = client.post("/api/auth/register", json={"name":"Candidate", "email":"user@test.example", "password":"safe-password-123"}).json()
    dashboard = client.get("/api/admin/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["stats"]["users"] == 2
    assert dashboard.json()["active_users_definition"]
    users = client.get("/api/admin/users?search=user%40test.example&limit=1", headers=admin_headers)
    assert users.json()["total"] == 1
    user_id = candidate["user"]["id"]
    changed = client.patch(f"/api/admin/users/{user_id}/role", json={"role":"admin"}, headers=admin_headers)
    assert changed.status_code == 200
    logs = client.get("/api/admin/activity-logs?action=user.role_changed", headers=admin_headers).json()
    assert logs["total"] == 1 and logs["logs"][0]["metadata"] == {"from":"candidate", "to":"admin"}
    assert client.get("/api/admin/dashboard",headers={"Authorization":f"Bearer {candidate['access_token']}"}).status_code==200
    assert client.patch(f"/api/admin/users/{user_id}/role",json={"role":"candidate"},headers=admin_headers).status_code==200
    assert client.get("/api/admin/dashboard",headers={"Authorization":f"Bearer {candidate['access_token']}"}).status_code==403


def test_last_active_admin_cannot_be_demoted_or_deactivated(client):
    session = client.post("/api/auth/register", json={"name":"Admin", "email":"only-admin@test.example", "password":"safe-password-123"}).json()
    headers = make_admin(session)
    uid = session["user"]["id"]
    assert client.patch(f"/api/admin/users/{uid}/role", json={"role":"candidate"}, headers=headers).status_code == 409
    assert client.patch(f"/api/admin/users/{uid}/status?is_active=false", headers=headers).status_code == 409


def test_company_learning_and_resource_validation_and_soft_delete(client):
    session = client.post("/api/auth/register", json={"name":"Admin", "email":"content-admin@test.example", "password":"safe-password-123"}).json()
    headers = make_admin(session)
    bad = client.post("/api/admin/companies", json={"name":"Acme", "website":"javascript:alert(1)", "source":{"source_type":"web","title":"source","url":"file:///etc/passwd"}}, headers=headers)
    assert bad.status_code == 422
    created = client.post("/api/admin/resources", json={"title":"Preparation","category":"Placement","resource_type":"article","url":"https://example.com/guide","is_active":True}, headers=headers)
    assert created.status_code == 201
    assert client.delete(f"/api/admin/resources/{created.json()['id']}", headers=headers).json()["is_active"] is False


def test_company_sources_learning_topics_and_questions_are_managed_without_physical_question_delete(client):
    session = client.post("/api/auth/register", json={"name":"Admin", "email":"editor@test.example", "password":"safe-password-123"}).json()
    headers = make_admin(session)
    company = client.post("/api/admin/companies", json={"name":"Example Works","industry":"Software","website":"https://example.com","source":{"source_type":"official","title":"About","url":"https://example.com/about","verification_status":"unverified"}}, headers=headers)
    assert company.status_code == 201
    cid = company.json()["id"]; source_id = company.json()["sources"][0]["id"]
    verified = client.patch(f"/api/admin/companies/sources/{source_id}/verification", json={"verification_status":"verified"}, headers=headers)
    assert verified.status_code == 200 and verified.json()["verification_status"] == "verified"
    cat = client.get("/api/admin/learning/categories", headers=headers).json()["categories"][0]
    topic = client.post("/api/admin/learning/topics", json={"category_id":cat["id"],"name":"Admin lesson","slug":"admin-lesson","description":"Lesson","content":{"sections":[]},"is_active":True}, headers=headers)
    assert topic.status_code == 201
    question = client.post("/api/admin/learning/questions", json={"topic_id":topic.json()["id"],"question":"Choose one","options":["A","B"],"correct_answer":1}, headers=headers)
    assert question.status_code == 201
    qid=question.json()["id"]
    assert client.delete(f"/api/admin/learning/questions/{qid}", headers=headers).json()["is_active"] is False
    listed=client.get(f"/api/admin/learning/questions?topic_id={topic.json()['id']}",headers=headers).json()
    assert listed["total"]==1 and listed["questions"][0]["is_active"] is False
    assert client.delete(f"/api/admin/companies/{cid}",headers=headers).json()["status"]=="inactive"


def test_learning_question_validation_and_interview_analytics(client):
    session = client.post("/api/auth/register", json={"name":"Admin", "email":"analytics-admin@test.example", "password":"safe-password-123"}).json()
    headers = make_admin(session)
    assert client.get("/api/admin/interviews/analytics", headers=headers).json()["total"] == 0
    assert client.post("/api/admin/learning/questions", json={"topic_id":1,"question":"Pick","options":["one","two"],"correct_answer":9}, headers=headers).status_code == 422


def test_phase9_migration_adds_role_and_audit_table_without_dropping_users():
    from app.db.migrations import ensure_phase9_admin_schema
    engine = create_engine("sqlite://", connect_args={"check_same_thread":False}, poolclass=StaticPool)
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL)")
        conn.exec_driver_sql("INSERT INTO users (id, name) VALUES (1, 'Existing')")
    ensure_phase9_admin_schema(engine)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("SELECT name, role FROM users").one() == ("Existing", "candidate")
    assert inspect(engine).has_table("admin_activity_logs")
    engine.dispose()


def test_admin_provisioning_requires_existing_active_account_and_password(client, monkeypatch):
    import sys
    from app.db import provision_admin
    session=client.post("/api/auth/register",json={"name":"Bootstrap","email":"bootstrap@test.example","password":"safe-password-123"}).json()
    monkeypatch.setattr(sys,"argv",["provision_admin","bootstrap@test.example"])
    monkeypatch.setattr(provision_admin,"SessionLocal",SessionLocal)
    monkeypatch.setattr(provision_admin.getpass,"getpass",lambda _:"wrong-password")
    import pytest
    with pytest.raises(SystemExit): provision_admin.main()
    with SessionLocal() as db: assert db.get(User,session["user"]["id"]).role=="candidate"
    monkeypatch.setattr(provision_admin.getpass,"getpass",lambda _:"safe-password-123")
    provision_admin.main()
    with SessionLocal() as db: assert db.get(User,session["user"]["id"]).role=="admin"
