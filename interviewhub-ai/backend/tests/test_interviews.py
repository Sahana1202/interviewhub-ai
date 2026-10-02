from datetime import timedelta

from app.db.database import SessionLocal
from app.models.interview import InterviewSession
from app.services.ai_service import AIService, AIServiceUnavailable
from app.services.interview_service import utc_now


def start_payload(**updates):
    return {
        "company_name": None,
        "job_role": "Full Stack Developer",
        "experience_level": "Fresher",
        "interview_type": "Combined",
        "difficulty": "Intermediate",
        "duration_minutes": 10,
        "interviewer_id": "aira",
        "response_mode": "text",
        **updates,
    }


def test_interview_routes_require_authentication(client):
    assert client.get("/api/interviews/interviewers").status_code == 401
    assert client.get("/api/interviews").status_code == 401
    assert client.post("/api/interviews/start", json=start_payload()).status_code == 401


def test_start_validates_setup_and_creates_starter_question(client, registered_user):
    headers = registered_user["headers"]
    interviewers = client.get("/api/interviews/interviewers", headers=headers)
    assert interviewers.status_code == 200
    assert [item["id"] for item in interviewers.json()] == ["aira", "arjun"]
    assert all("Virtual" in item["role"] for item in interviewers.json())

    started = client.post("/api/interviews/start", headers=headers, json=start_payload(company_name="Example Labs"))
    assert started.status_code == 201, started.text
    body = started.json()
    assert body["question_source"] == "starter_bank"
    assert body["session"]["status"] == "in_progress"
    assert body["session"]["company_name"] == "Example Labs"
    assert body["session"]["interviewer_name"] == "SIRI"
    assert body["session"]["question_count"] == 1
    assert body["current_question"]["sequence_number"] == 1
    assert body["current_question"]["category"] == "Introduction"
    assert body["current_question"]["question_text"] == "Tell me about yourself."

    assert client.post("/api/interviews/start", headers=headers, json=start_payload(interviewer_id="unknown")).status_code == 422
    assert client.post("/api/interviews/start", headers=headers, json=start_payload(duration_minutes=5)).status_code == 422
    assert client.post("/api/interviews/start", headers=headers, json=start_payload(interview_type="Unsupported")).status_code == 422
    assert client.post("/api/interviews/start", headers=headers, json=start_payload(difficulty="Impossible")).status_code == 422
    assert client.post("/api/interviews/start", headers=headers, json=start_payload(response_mode="video")).status_code == 422
    assert client.post("/api/interviews/start", headers=headers, json=start_payload(experience_level="10 years")).status_code == 422
    assert client.post("/api/interviews/start", headers=headers, json=start_payload(job_role=" ")).status_code == 422


def test_interview_ownership_answers_and_history(client, registered_user):
    first_headers = registered_user["headers"]
    second_response = client.post("/api/auth/register", json={"name": "Other Candidate", "email": "other@example.com", "password": "safe-password-123"})
    assert second_response.status_code == 201
    second_headers = {"Authorization": f"Bearer {second_response.json()['access_token']}"}
    started = client.post("/api/interviews/start", headers=first_headers, json=start_payload())
    session_id = started.json()["session"]["id"]
    question = started.json()["current_question"]

    assert client.get(f"/api/interviews/{session_id}", headers=first_headers).status_code == 200
    assert client.get(f"/api/interviews/{session_id}", headers=second_headers).status_code == 404
    assert client.post(f"/api/interviews/{session_id}/answer", headers=second_headers, json={"question_id": question["id"], "answer_text": "hello", "response_mode": "text"}).status_code == 404
    assert client.post(f"/api/interviews/{session_id}/pause", headers=second_headers).status_code == 404
    assert client.post(f"/api/interviews/{session_id}/complete", headers=second_headers).status_code == 404

    empty = client.post(f"/api/interviews/{session_id}/answer", headers=first_headers, json={"question_id": question["id"], "answer_text": "  ", "response_mode": "text"})
    assert empty.status_code == 422
    wrong_question = client.post(f"/api/interviews/{session_id}/answer", headers=first_headers, json={"question_id": 9999, "answer_text": "Answer", "response_mode": "text"})
    assert wrong_question.status_code == 409
    wrong_mode = client.post(f"/api/interviews/{session_id}/answer", headers=first_headers, json={"question_id": question["id"], "answer_text": "Answer", "response_mode": "voice"})
    assert wrong_mode.status_code == 422

    saved = client.post(f"/api/interviews/{session_id}/answer", headers=first_headers, json={"question_id": question["id"], "answer_text": "I am a software engineering candidate.", "response_mode": "text", "duration_seconds": 35})
    assert saved.status_code == 200, saved.text
    assert saved.json()["saved_answer"]["answer_text"].startswith("I am")
    assert saved.json()["next_question"]["sequence_number"] == 2
    assert saved.json()["session"]["answers_count"] == 1
    assert client.post(f"/api/interviews/{session_id}/answer", headers=first_headers, json={"question_id": question["id"], "answer_text": "duplicate", "response_mode": "text"}).status_code == 409

    paused = client.post(f"/api/interviews/{session_id}/pause", headers=first_headers)
    assert paused.status_code == 200 and paused.json()["status"] == "paused"
    current_question = paused.json()["questions"][-1]
    assert client.post(f"/api/interviews/{session_id}/answer", headers=first_headers, json={"question_id": current_question["id"], "answer_text": "paused attempt", "response_mode": "text"}).status_code == 409
    resumed = client.post(f"/api/interviews/{session_id}/pause", headers=first_headers)
    assert resumed.status_code == 200 and resumed.json()["status"] == "in_progress"
    completed = client.post(f"/api/interviews/{session_id}/complete", headers=first_headers)
    assert completed.status_code == 200 and completed.json()["status"] == "completed"
    assert completed.json()["answers_count"] == 1
    assert completed.json()["completed_at"] is not None
    assert client.post(f"/api/interviews/{session_id}/pause", headers=first_headers).status_code == 409

    first_history = client.get("/api/interviews", headers=first_headers).json()["sessions"]
    second_history = client.get("/api/interviews", headers=second_headers).json()["sessions"]
    assert [row["id"] for row in first_history] == [session_id]
    assert second_history == []
    assert client.get(f"/api/interviews/{session_id}", headers=first_headers).json()["questions"][0]["answer"]["duration_seconds"] == 35


def test_question_bank_sequences_without_duplicates(client, registered_user):
    headers = registered_user["headers"]
    started = client.post("/api/interviews/start", headers=headers, json=start_payload(interviewer_id="arjun", interview_type="Combined"))
    assert started.status_code == 201
    session = started.json()["session"]
    current = started.json()["current_question"]
    questions = [current["question_text"]]
    categories = [current["category"]]
    while True:
        response = client.post(f"/api/interviews/{session['id']}/answer", headers=headers, json={
            "question_id": current["id"], "answer_text": f"Practice answer for question {current['sequence_number']}", "response_mode": "text",
        })
        assert response.status_code == 200, response.text
        current = response.json()["next_question"]
        if current is None:
            assert response.json()["question_set_complete"] is True
            break
        questions.append(current["question_text"])
        categories.append(current["category"])
    assert len(questions) == 5
    assert len(set(questions)) == len(questions)
    assert categories[:3] == ["Introduction", "HR", "Technical"]


def test_empty_interview_history_is_real_empty_list(client, registered_user):
    assert client.get("/api/interviews", headers=registered_user["headers"]).json() == {"sessions": []}


def test_interview_timer_and_answer_persist_when_session_time_expires(client, registered_user):
    headers = registered_user["headers"]
    started = client.post("/api/interviews/start", headers=headers, json=start_payload())
    details = started.json()
    session_id = details["session"]["id"]
    db = SessionLocal()
    session = db.get(InterviewSession, session_id)
    session.started_at = utc_now() - timedelta(minutes=11)
    db.commit()
    db.close()

    expired = client.get(f"/api/interviews/{session_id}", headers=headers).json()
    assert expired["remaining_seconds"] == 0
    answer = client.post(f"/api/interviews/{session_id}/answer", headers=headers, json={
        "question_id": details["current_question"]["id"],
        "answer_text": "This answer arrived at the end of the timer.",
        "response_mode": "text",
    })
    assert answer.status_code == 200
    assert answer.json()["session"]["status"] == "completed"
    assert answer.json()["session"]["remaining_seconds"] == 0
    assert answer.json()["session"]["answers_count"] == 1


def test_hr_question_set_stays_within_its_configured_categories(client, registered_user):
    headers = registered_user["headers"]
    started = client.post("/api/interviews/start", headers=headers, json=start_payload(interview_type="HR", duration_minutes=30))
    current = started.json()["current_question"]
    categories = [current["category"]]
    questions = [current["question_text"]]
    while True:
        result = client.post(f"/api/interviews/{started.json()['session']['id']}/answer", headers=headers, json={
            "question_id": current["id"], "answer_text": "A practice response.", "response_mode": "text",
        }).json()
        current = result["next_question"]
        if current is None:
            break
        categories.append(current["category"])
        questions.append(current["question_text"])
    assert set(categories) <= {"Introduction", "HR", "Behavioral", "Situational"}
    assert len(questions) == len(set(questions))
    assert len(questions) == 8


def test_future_ai_service_fails_explicitly():
    service = AIService()
    for feature in (service.generate_question, service.generate_followup, service.evaluate_answer, service.generate_report):
        try:
            feature()
        except AIServiceUnavailable as error:
            assert "no AI provider is configured" in str(error)
        else:
            raise AssertionError("An AI method must not return a simulated result")


def test_voice_transcript_is_saved_as_an_editable_answer(client, registered_user):
    headers = registered_user["headers"]
    started = client.post("/api/interviews/start", headers=headers, json=start_payload(interviewer_id="arjun", response_mode="voice"))
    question = started.json()["current_question"]
    transcript = "I planned the work, tested each change, and reviewed the result."
    answer = client.post(f"/api/interviews/{started.json()['session']['id']}/answer", headers=headers, json={
        "question_id": question["id"], "transcript": transcript, "response_mode": "voice", "duration_seconds": 22,
    })
    assert answer.status_code == 200, answer.text
    saved = answer.json()["saved_answer"]
    assert saved["response_mode"] == "voice"
    assert saved["answer_text"] == transcript
    assert saved["transcript"] == transcript
    assert saved["duration_seconds"] == 22
