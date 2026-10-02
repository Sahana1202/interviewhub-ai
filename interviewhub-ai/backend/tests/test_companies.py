import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.company import Company, CompanySource, CompanyTechnology, CompanyRole, CompanyInterviewTopic
from app.models.interview import InterviewSession
from app.services.company_service import ingest_company, normalize_name


def add_company(name="Test Company", status="verified", facts=None):
    with Session(engine) as db:
        return ingest_company(db, name=name, source={"source_type": "official_document", "title": "Test source",
            "url": "https://example.org/company", "publisher": "Test Publisher", "verification_status": status}, facts=facts or {})


def test_name_normalization_and_duplicate_ingestion(client):
    assert normalize_name("  Ｔｅｓｔ   COMPANY ") == "test company"
    first = add_company("Test Company")
    second = add_company("TEST COMPANY")
    assert first.id == second.id
    assert client.get("/api/companies?q=test", headers={}).status_code == 401


def test_ingestion_rejects_unsafe_urls(client):
    with Session(engine) as db, pytest.raises(ValueError):
        ingest_company(db, name="Unsafe Test", source={"source_type": "official_website", "title": "Bad source", "url": "javascript:alert(1)"})
    with Session(engine) as db, pytest.raises(ValueError):
        ingest_company(db, name="Unsafe Test", source={"source_type": "official_website", "title": "Good source", "url": "https://example.org"}, facts={"website": "javascript:alert(1)"})


def test_company_search_detail_sources_and_context(client, registered_user):
    company = add_company(facts={"industry": "Testing", "founded_year": 2001, "website": "https://example.org"})
    with Session(engine) as db:
        source = db.query(CompanySource).filter_by(company_id=company.id).first()
        db.add(CompanyTechnology(company_id=company.id, technology="Python", category="Programming", source_id=source.id))
        db.add(CompanyRole(company_id=company.id, role_title="Test Engineer", skills=["Python"], source_id=source.id, status="historical"))
        db.add(CompanyInterviewTopic(company_id=company.id, topic="SQL", category="SQL", source_id=source.id, verification_status="verified"))
        db.commit()
    headers = registered_user["headers"]
    result = client.get("/api/companies/search?q=TEST", headers=headers)
    assert result.status_code == 200 and result.json()["companies"][0]["name"] == "Test Company"
    detail = client.get(f"/api/companies/{company.id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["technologies"][0]["technology"] == "Python"
    assert body["roles"][0]["status"] == "historical"
    assert body["sources"][0]["verification_status"] == "verified"
    context = client.get(f"/api/companies/{company.id}/interview-context", headers=headers)
    assert context.status_code == 200 and context.json()["reported_interview_topics"][0]["topic"] == "SQL"
    assert client.get("/api/companies/9999", headers=headers).status_code == 404


def test_bookmark_user_ownership(client, registered_user):
    company = add_company()
    first = registered_user["headers"]
    second_user = client.post("/api/auth/register", json={"name": "Second", "email": "second@example.com", "password": "safe-password-123"}).json()
    second = {"Authorization": f"Bearer {second_user['access_token']}"}
    assert client.post(f"/api/companies/{company.id}/bookmark", headers=first).status_code == 204
    assert len(client.get("/api/companies/bookmarks", headers=first).json()["companies"]) == 1
    assert client.get("/api/companies/bookmarks", headers=second).json()["companies"] == []
    assert client.delete(f"/api/companies/{company.id}/bookmark", headers=second).status_code == 204
    assert len(client.get("/api/companies/bookmarks", headers=first).json()["companies"]) == 1
    assert client.delete(f"/api/companies/{company.id}/bookmark", headers=first).status_code == 204


def test_quiz_requires_verified_fact_and_hides_answer_until_submit(client, registered_user):
    company = add_company(status="needs_verification", facts={"founded_year": 1999})
    headers = registered_user["headers"]
    assert client.get(f"/api/companies/{company.id}/quiz", headers=headers).status_code == 404
    verified = add_company("Verified Test Org", facts={"founded_year": 2001})
    response = client.get(f"/api/companies/{verified.id}/quiz", headers=headers)
    assert response.status_code == 200
    question = response.json()
    assert "correct_answer" not in question and "explanation" not in question
    assert question["label"] == "Company Knowledge Practice"
    answer = client.post(f"/api/companies/{verified.id}/quiz/answer", headers=headers,
                         json={"question_id": question["id"], "selected_answer": question["options"].index("2001")})
    assert answer.status_code == 200 and answer.json()["correct"] is True
    assert answer.json()["attempted"] == 1 and answer.json()["correct_count"] == 1
    assert client.post(f"/api/companies/{verified.id}/quiz/answer", headers=headers,
                       json={"question_id": question["id"], "selected_answer": 8}).status_code == 422


def test_interview_optional_company_reference_and_safe_delete(client, registered_user):
    company = add_company()
    headers = registered_user["headers"]
    payload = {"company_id": company.id, "job_role": "Backend Developer", "experience_level": "Fresher",
        "interview_type": "HR", "difficulty": "Beginner", "duration_minutes": 10,
        "interviewer_id": "aira", "response_mode": "text"}
    # Use the actual configured interviewer identifier supplied by the API.
    interviewer = client.get("/api/interviews/interviewers", headers=headers).json()[0]
    payload["interviewer_id"] = interviewer["id"]
    created = client.post("/api/interviews/start", headers=headers, json=payload)
    assert created.status_code == 201 and created.json()["session"]["company_id"] == company.id
    legacy = dict(payload, company_id=None)
    legacy.pop("company_name", None)
    created_legacy = client.post("/api/interviews/start", headers=headers, json=legacy)
    assert created_legacy.status_code == 201 and created_legacy.json()["session"]["company_id"] is None
    with Session(engine) as db:
        db.delete(db.get(Company, company.id))
        db.commit()
        session = db.get(InterviewSession, created.json()["session"]["id"])
        assert session.company_id is None
