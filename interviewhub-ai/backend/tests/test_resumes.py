import fitz
import pytest
from pathlib import Path
from sqlalchemy import create_engine, inspect, text

from app.services import resume_service


@pytest.fixture(autouse=True)
def use_temp_resume_storage(monkeypatch):
    root = Path(__file__).resolve().parent / ".phase5-resume-storage"
    root.mkdir(exist_ok=True)
    for path in root.rglob("*"):
        if path.is_file():
            path.unlink()
    monkeypatch.setattr(resume_service, "STORAGE_ROOT", root)
    yield
    for path in root.rglob("*"):
        if path.is_file():
            path.unlink()


def register(client, email):
    response = client.post("/api/auth/register", json={"name": "Test Candidate", "email": email, "password": "safe-password-123"})
    assert response.status_code == 201
    return response.json()


def pdf_bytes(text: str = "") -> bytes:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((50, 50), text, fontsize=10)
    data = document.tobytes()
    document.close()
    return data


def upload(client, headers, data=None, name="resume.pdf"):
    return client.post("/api/resumes/upload", headers=headers,
                       files={"file": (name, data if data is not None else pdf_bytes(), "application/pdf")})


def test_resume_requires_authentication(client):
    response = client.post("/api/resumes/upload", files={"file": ("resume.pdf", pdf_bytes(), "application/pdf")})
    assert response.status_code == 401


def test_resume_endpoints_require_authentication(client):
    assert client.get("/api/resumes").status_code == 401
    assert client.get("/api/resumes/1").status_code == 401
    assert client.get("/api/resumes/1/interview-context").status_code == 401
    assert client.post("/api/resumes/1/analyze").status_code == 401
    assert client.delete("/api/resumes/1").status_code == 401


def test_existing_interview_table_gets_nullable_resume_column_without_data_loss():
    from app.db.migrations import ensure_interview_resume_column

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE interview_sessions (id INTEGER PRIMARY KEY, job_role VARCHAR(120) NOT NULL)"))
        connection.execute(text("INSERT INTO interview_sessions (id, job_role) VALUES (1, 'Engineer')"))
    ensure_interview_resume_column(engine)
    assert "resume_id" in {column["name"] for column in inspect(engine).get_columns("interview_sessions")}
    with engine.connect() as connection:
        role, resume_id = connection.execute(text("SELECT job_role, resume_id FROM interview_sessions WHERE id=1")).one()
    assert role == "Engineer" and resume_id is None
    engine.dispose()


def test_upload_rejects_extension_and_pdf_content(client, registered_user):
    headers = registered_user["headers"]
    assert upload(client, headers, name="resume.docx").status_code == 415
    assert upload(client, headers, data=b"not a PDF").status_code == 422


def test_upload_rejects_oversized_file(client, registered_user):
    response = upload(client, registered_user["headers"], data=b"%PDF-" + b"x" * (10 * 1024 * 1024))
    assert response.status_code == 413


def test_resume_extracts_structured_data_and_completeness(client, registered_user):
    source = """Maya Candidate
maya@example.com | https://github.com/maya-candidate
Education
B.Tech Computer Science, Example University, 2025, CGPA: 8.4
Technical Skills
Python, React, FastAPI, MySQL, Git
Academic Projects
Campus Event Hub - Built an event app with React and FastAPI
Work Experience
Software Intern at Example Labs 2024-2025 - Developed Python services
Certifications
AWS Cloud Practitioner
Achievements
Hackathon finalist
"""
    response = upload(client, registered_user["headers"], data=pdf_bytes(source), name="../Maya Resume.pdf")
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["file_name"] == "Maya Resume.pdf"
    assert created["status"] == "processed"
    detail = client.get(f"/api/resumes/{created['id']}", headers=registered_user["headers"])
    assert detail.status_code == 200
    body = detail.json()
    assert body["contact"]["name"] == "Maya Candidate"
    assert body["contact"]["email"] == "maya@example.com"
    assert body["contact"]["phone"] is None
    assert body["education"] and "B.Tech" in body["education"][0]["degree"]
    assert body["education"][0]["institution"] == "Example University"
    assert {"Python", "React", "FastAPI", "MySQL"}.issubset(set(body["skills"]))
    assert body["projects"][0]["name"] == "Campus Event Hub"
    assert "Built an event app" in body["projects"][0]["description"]
    assert body["experience"] and body["experience"][0]["dates"] == "2024-2025"
    assert body["experience"][0]["organization"] == "Example Labs"
    assert body["certifications"] == ["AWS Cloud Practitioner"]
    assert body["completeness"]["checks"]["skills"] is True
    assert body["practice_questions"]
    assert "extracted_text" not in body
    assert "sections" not in body
    assert "file_path" not in body and "stored_file_name" not in body
    assert client.get("/api/resumes", headers=registered_user["headers"]).json()[0]["id"] == created["id"]


def test_empty_or_scanned_pdf_is_not_reported_as_processed(client, registered_user):
    response = upload(client, registered_user["headers"], data=pdf_bytes())
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert "scanned or image-based" in response.json()["processing_message"]
    detail = client.get(f"/api/resumes/{response.json()['id']}", headers=registered_user["headers"]).json()
    assert detail["skills"] == []
    assert client.post(f"/api/resumes/{response.json()['id']}/analyze", headers=registered_user["headers"]).status_code == 422


def test_resume_path_traversal_and_corrupt_pdf_are_contained(client, registered_user):
    headers=registered_user["headers"]
    malicious=upload(client,headers,data=pdf_bytes("Technical Skills\nPython"),name="..\\..\\something.pdf")
    assert malicious.status_code==201
    assert malicious.json()["file_name"]=="something.pdf"
    detail=client.get(f"/api/resumes/{malicious.json()['id']}",headers=headers)
    assert detail.status_code==200 and "file_path" not in detail.text and "sections" not in detail.json()
    corrupt=upload(client,headers,data=b"%PDF-not-a-valid-document",name="bad.pdf")
    assert corrupt.status_code==422


def test_resume_ownership_context_and_delete(client, registered_user):
    own = upload(client, registered_user["headers"], data=pdf_bytes("Technical Skills\nPython" )).json()
    other = register(client, "other-candidate@example.com")
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.get(f"/api/resumes/{own['id']}", headers=other_headers).status_code == 404
    assert client.get(f"/api/resumes/{own['id']}/interview-context", headers=other_headers).status_code == 404
    assert client.delete(f"/api/resumes/{own['id']}", headers=other_headers).status_code == 404
    context = client.get(f"/api/resumes/{own['id']}/interview-context", headers=registered_user["headers"])
    assert context.status_code == 200 and context.json()["skills"] == ["Python"]
    assert client.delete(f"/api/resumes/{own['id']}", headers=registered_user["headers"]).status_code == 204
    assert client.get(f"/api/resumes/{own['id']}", headers=registered_user["headers"]).status_code == 404


def test_interview_can_reference_only_owned_resume(client, registered_user):
    own = upload(client, registered_user["headers"], data=pdf_bytes("Technical Skills\nPython")).json()
    payload = {"job_role": "Software Engineer", "experience_level": "Fresher", "interview_type": "HR",
               "difficulty": "Beginner", "duration_minutes": 10, "interviewer_id": "aira",
               "response_mode": "text", "resume_id": own["id"]}
    started = client.post("/api/interviews/start", json=payload, headers=registered_user["headers"])
    assert started.status_code == 201, started.text
    assert started.json()["session"]["resume_id"] == own["id"]
    session_id = started.json()["session"]["id"]
    assert started.json()["session"]["resume_file_name"] == "resume.pdf"
    assert client.delete(f"/api/resumes/{own['id']}", headers=registered_user["headers"]).status_code == 204
    detached = client.get(f"/api/interviews/{session_id}", headers=registered_user["headers"])
    assert detached.json()["resume_id"] is None and detached.json()["resume_file_name"] is None
    other = register(client, "other-resume-owner@example.com")
    payload["resume_id"] = 99999
    denied = client.post("/api/interviews/start", json=payload, headers={"Authorization": f"Bearer {other['access_token']}"})
    assert denied.status_code == 404
