from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.company import Company, CompanyInterviewTopic, CompanySource, UserCompanyBookmark
from app.models.learning import LearningCategory, LearningProgress, LearningResource, LearningTopic, PracticeAttempt, PracticeAttemptAnswer, PracticeQuestion
from app.models.resume import Resume
from app.models.user import User
from app.services.learning_seed_service import seed_learning_catalog


def another_user(client):
    response = client.post("/api/auth/register", json={"name": "Other Candidate", "email": "other-learning@example.com", "password": "safe-password-123"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def topic_by_name(name):
    with Session(engine) as db:
        return db.scalar(select(LearningTopic).where(LearningTopic.name == name))


def test_learning_categories_topics_content_and_idempotent_seed(client, registered_user):
    headers = registered_user["headers"]
    response = client.get("/api/learning/categories", headers=headers)
    assert response.status_code == 200
    categories = response.json()["categories"]
    assert {item["slug"] for item in categories} >= {"technical", "hr", "aptitude", "professional-english", "placement-resources"}
    technical = next(item for item in categories if item["slug"] == "technical")
    detail = client.get(f"/api/learning/categories/{technical['id']}", headers=headers).json()
    names = {item["name"] for item in detail["topics"]}
    assert {"Variables & Data Types", "JOINs", "Normalization", "Arrays", "HTML", "Git & GitHub"} <= names
    python_topic = next(item for item in detail["topics"] if item["name"] == "Object-Oriented Programming")
    full = client.get(f"/api/learning/topics/{python_topic['id']}", headers=headers).json()
    assert all(key in full["content"] for key in ("definition", "why_it_matters", "simple_explanation", "example", "key_interview_points", "quick_revision", "practice_prompts"))
    before = len(detail["topics"])
    with Session(engine) as db:
        seed_learning_catalog(db)
        assert db.scalar(select(func.count(LearningTopic.id)).where(LearningTopic.category_id == technical["id"])) == before


def test_topic_completion_is_explicit_and_progress_is_user_scoped(client, registered_user):
    headers = registered_user["headers"]
    other = another_user(client)
    topic = topic_by_name("Variables & Data Types")
    assert client.get(f"/api/learning/progress/{topic.id}", headers=headers).json()["progress_percent"] == 0
    assert client.post(f"/api/learning/topics/{topic.id}/complete", headers=headers).status_code == 200
    own = client.get("/api/learning/progress", headers=headers).json()["progress"][0]
    assert own["completed"] is True and own["progress_percent"] == 100
    assert client.get(f"/api/learning/progress/{topic.id}", headers=other).json()["progress_percent"] == 0
    assert client.post(f"/api/learning/topics/99999/complete", headers=headers).status_code == 404
    assert client.get("/api/learning/categories").status_code == 401


def test_practice_hides_answer_scores_server_side_and_prevents_duplicate_or_completed_edits(client, registered_user):
    headers = registered_user["headers"]
    topic = topic_by_name("Functions")
    started = client.post("/api/practice/start", headers=headers, json={"topic_id": topic.id, "difficulty": "Easy", "question_count": 2})
    assert started.status_code == 201
    attempt = started.json()
    first = attempt["current_question"]
    assert "correct_answer" not in first and "correct_option" not in first and "explanation" not in first
    with Session(engine) as db:
        correct_index = db.get(PracticeQuestion, first["id"]).correct_answer
    wrong = (correct_index + 1) % 4
    first_answer = client.post(f"/api/practice/{attempt['id']}/answer", headers=headers, json={"question_id": first["id"], "selected_answer": wrong})
    assert first_answer.status_code == 200 and first_answer.json()["correct"] is False
    assert first_answer.json()["explanation"] and first_answer.json()["correct_option"]
    assert client.post(f"/api/practice/{attempt['id']}/answer", headers=headers, json={"question_id": first["id"], "selected_answer": wrong}).status_code == 409
    second = first_answer.json()["next_question"]
    with Session(engine) as db:
        right_index = db.get(PracticeQuestion, second["id"]).correct_answer
    last = client.post(f"/api/practice/{attempt['id']}/answer", headers=headers, json={"question_id": second["id"], "selected_answer": right_index})
    assert last.status_code == 200 and last.json()["completed"] is True
    assert last.json()["attempt"]["correct_answers"] == 1
    assert last.json()["attempt"]["incorrect_answers"] == 1
    assert last.json()["attempt"]["accuracy"] == 50
    assert last.json()["attempt"]["review"][0]["correct_option"]
    assert client.post(f"/api/practice/{attempt['id']}/answer", headers=headers, json={"question_id": second["id"], "selected_answer": right_index}).status_code == 409
    progress = client.get(f"/api/learning/progress/{topic.id}", headers=headers).json()
    assert progress["questions_attempted"] == 2 and progress["questions_correct"] == 1
    history = client.get("/api/practice/history", headers=headers).json()["attempts"]
    assert history[0]["accuracy"] == 50


def test_practice_ownership_invalid_filters_and_question_membership(client, registered_user):
    headers = registered_user["headers"]
    other = another_user(client)
    topic = topic_by_name("Functions")
    attempt = client.post("/api/practice/start", headers=headers, json={"topic_id": topic.id, "question_count": 2}).json()
    assert client.get(f"/api/practice/{attempt['id']}", headers=other).status_code == 404
    assert client.post(f"/api/practice/{attempt['id']}/complete", headers=other).status_code == 404
    assert client.get("/api/practice/history", headers=other).json()["attempts"] == []
    assert client.post("/api/practice/start", headers=headers, json={"topic_id": topic.id, "category_id": 99999}).status_code == 422
    assert client.post("/api/practice/start", headers=headers, json={"topic_id": topic.id, "difficulty": "Hard"}).status_code == 404
    foreign_topic = topic_by_name("JOINs")
    foreign_q = client.post("/api/practice/start", headers=headers, json={"topic_id": foreign_topic.id, "question_count": 1}).json()["current_question"]
    assert client.post(f"/api/practice/{attempt['id']}/answer", headers=headers, json={"question_id": foreign_q["id"], "selected_answer": 0}).status_code == 404


def test_medium_practice_and_low_accuracy_recommendation(client, registered_user):
    headers = registered_user["headers"]
    topic = topic_by_name("Probability")
    detail = client.get(f"/api/learning/topics/{topic.id}", headers=headers).json()
    assert {item["difficulty"] for item in detail["practice_options"]} == {"Medium"}
    attempt = client.post("/api/practice/start", headers=headers, json={"topic_id": topic.id, "difficulty": "Medium", "question_count": 1}).json()
    current = attempt["current_question"]
    with Session(engine) as db:
        answer = (db.get(PracticeQuestion, current["id"]).correct_answer + 1) % 4
    result = client.post(f"/api/practice/{attempt['id']}/answer", headers=headers,
        json={"question_id": current["id"], "selected_answer": answer})
    assert result.status_code == 200 and result.json()["completed"] is True
    recommendations = client.get("/api/learning/recommendations", headers=headers).json()["recommended_topics"]
    probability = next(item for item in recommendations if item["topic_id"] == topic.id)
    assert "recent practice accuracy is lower" in probability["reason"]


def test_finishing_early_counts_unanswered_without_calling_them_wrong(client, registered_user):
    headers = registered_user["headers"]
    topic = topic_by_name("Functions")
    started = client.post("/api/practice/start", headers=headers,
        json={"topic_id": topic.id, "difficulty": "Easy", "question_count": 2}).json()
    question = started["current_question"]
    with Session(engine) as db:
        right_answer = db.get(PracticeQuestion, question["id"]).correct_answer
    answer = client.post(f"/api/practice/{started['id']}/answer", headers=headers,
        json={"question_id": question["id"], "selected_answer": right_answer})
    assert answer.status_code == 200
    completed = client.post(f"/api/practice/{started['id']}/complete", headers=headers).json()
    assert completed["correct_answers"] == 1 and completed["incorrect_answers"] == 0
    assert completed["unanswered_count"] == 1 and completed["accuracy"] == 50
    skipped = next(item for item in completed["review"] if not item["answered"])
    assert skipped["correct_option"] and skipped["explanation"]


def test_resume_and_career_goal_recommendations_and_company_topics(client, registered_user):
    headers = registered_user["headers"]
    user_id = registered_user["session"]["user"]["id"]
    with Session(engine) as db:
        user = db.get(User, user_id)
        user.profile.target_role = "Python Developer"
        resume = Resume(user_id=user_id, file_name="candidate.pdf", stored_file_name="recommendation-test.pdf",
            file_path="/nonexistent/test.pdf", file_size=1, parsed_data={"skills": ["Python"]}, status="processed")
        db.add(resume)
        company = Company(name="Saved Test Employer", normalized_name="saved test employer")
        db.add(company)
        db.flush()
        source = CompanySource(company_id=company.id, source_type="official_document", title="Test source",
            url="https://example.org/verified", verification_status="verified")
        db.add(source)
        db.flush()
        db.add(CompanyInterviewTopic(company_id=company.id, topic="SQL discussion", category="SQL",
            source_id=source.id, verification_status="publicly_reported"))
        db.add(UserCompanyBookmark(user_id=user_id, company_id=company.id))
        db.commit()
    result = client.get("/api/learning/recommendations", headers=headers)
    assert result.status_code == 200
    body = result.json()
    assert body["career_goal"] == "Python Developer"
    assert body["resume_skills"] == ["python"]
    assert any("Python" in item["topic"] for item in body["recommended_topics"])
    assert body["company_preparation"]["topics"][0]["verification_status"] == "publicly_reported"
    assert client.get("/api/learning/recommendations", headers=another_user(client)).json()["company_preparation"]["company_id"] is None


def test_resource_filtering_and_private_resource_ownership(client, registered_user):
    headers = registered_user["headers"]
    other = another_user(client)
    owner_id = registered_user["session"]["user"]["id"]
    other_id = int(client.get("/api/auth/me", headers=other).json()["id"])
    with Session(engine) as db:
        public = LearningResource(title="Public Python guide", description="Internal guide", category="Technical", resource_type="internal", source="internal")
        private = LearningResource(title="Private note", description="Owner-only", category="Technical", resource_type="internal", source="internal", user_id=owner_id)
        other_private = LearningResource(title="Other private note", description="Not for this user", category="Technical", resource_type="internal", source="internal", user_id=other_id)
        db.add_all([public, private, other_private])
        db.commit()
        other_private_id = other_private.id
    owner_rows = client.get("/api/resources", headers=headers, params={"category": "technical", "search": "Python"})
    assert len(owner_rows.json()["resources"]) == 1
    all_owner = client.get("/api/resources", headers=headers).json()["resources"]
    assert {item["title"] for item in all_owner} == {"Public Python guide", "Private note"}
    assert client.get(f"/api/resources/{other_private_id}", headers=headers).status_code == 404
    assert client.get(f"/api/resources/{other_private_id}", headers=other).status_code == 200
    assert client.get("/api/resources", headers=other).json()["placement_source"]["import_configured"] is False


def test_placement_resource_boundary_has_no_fabricated_imports(client, registered_user):
    result = client.get("/api/resources", headers=registered_user["headers"]).json()
    assert result["resources"] == []
    assert result["placement_source"]["import_configured"] is False
    assert "import" in result["placement_source"]["message"].lower()
