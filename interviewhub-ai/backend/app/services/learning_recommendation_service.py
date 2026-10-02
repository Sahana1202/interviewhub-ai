from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.company import Company, CompanyInterviewTopic, UserCompanyBookmark
from app.models.learning import LearningCategory, LearningProgress, LearningTopic, PracticeAttempt
from app.models.resume import Resume

ROLE_TERMS = {
    "python": ["python", "object-oriented-programming", "sql", "dbms", "arrays", "web-development", "git-github"],
    "developer": ["python", "object-oriented-programming", "sql", "dbms", "arrays", "web-development", "git-github"],
    "software": ["python", "object-oriented-programming", "sql", "dbms", "arrays", "web-development", "git-github"],
    "data": ["python", "sql", "dbms", "data-structures", "probability", "data-interpretation"],
    "analyst": ["sql", "dbms", "data-interpretation", "percentages", "averages"],
}


def build_recommendations(db: Session, user_id: int, target_role: str | None) -> dict:
    topics = db.scalars(select(LearningTopic).where(LearningTopic.is_active.is_(True)).order_by(LearningTopic.display_order)).all()
    progress_rows = db.scalars(select(LearningProgress).where(LearningProgress.user_id == user_id)).all()
    progress = {item.topic_id: item for item in progress_rows}
    attempts = db.scalars(select(PracticeAttempt).where(PracticeAttempt.user_id == user_id, PracticeAttempt.status == "completed").order_by(PracticeAttempt.completed_at.desc())).all()
    recent = {}
    for attempt in attempts:
        recent.setdefault(attempt.topic_id, []).append(attempt.accuracy)
    role_text = (target_role or "").casefold()
    role_slugs = {slug for term, slugs in ROLE_TERMS.items() if term in role_text for slug in slugs}
    low_accuracy = [topic_id for topic_id, scores in recent.items() if len(scores) >= 1 and sum(scores[:5]) / min(5, len(scores)) < 70]
    incomplete = [topic for topic in topics if not progress.get(topic.id) or not progress[topic.id].completed]

    resume_skills = set()
    resumes = db.scalars(select(Resume).where(Resume.status == "processed", Resume.user_id == user_id).order_by(Resume.created_at.desc()).limit(1)).all()
    if resumes:
        resume_skills = {str(skill).casefold() for skill in resumes[0].parsed_data.get("skills", [])}

    ranked = []
    for topic in incomplete:
        accuracy = recent.get(topic.id, [])
        skill_match = any(topic.name.casefold() in skill or skill in topic.name.casefold() for skill in resume_skills)
        role_match = topic.slug in role_slugs
        progress_item = progress.get(topic.id)
        lower_recent_accuracy = bool(accuracy and sum(accuracy[:5]) / min(5, len(accuracy)) < 70)
        if progress_item and progress_item.progress_percent > 0 and lower_recent_accuracy:
            reason, priority = "Continue this topic; your recent practice accuracy is lower here.", 0
        elif progress_item and progress_item.progress_percent > 0:
            reason, priority = "Continue the topic you started.", 0
        elif lower_recent_accuracy:
            reason, priority = "Recommended because your recent practice accuracy is lower on this topic.", 1
        elif role_match:
            reason, priority = f"Related to your career goal: {target_role}.", 2
        elif skill_match:
            reason, priority = "Related to a skill listed in your processed resume; this does not indicate proficiency.", 3
        else:
            reason, priority = "A useful next step for general placement preparation.", 4
        ranked.append((priority, topic.display_order, topic, reason))
    ranked.sort(key=lambda row: (row[0], row[1]))
    recommended = [{"topic_id": topic.id, "topic": topic.name, "category_id": topic.category_id, "reason": reason} for _, _, topic, reason in ranked[:5]]

    company = db.scalar(select(Company).join(UserCompanyBookmark, UserCompanyBookmark.company_id == Company.id)
        .where(UserCompanyBookmark.user_id == user_id, Company.status == "active").order_by(Company.name).limit(1))
    company_topics = []
    if company:
        company_topics = [{"topic": row.topic, "category": row.category, "verification_status": row.verification_status}
            for row in db.scalars(select(CompanyInterviewTopic).where(CompanyInterviewTopic.company_id == company.id).limit(12)).all()]
    return {"career_goal": target_role or "General Placement Preparation", "recommended_topics": recommended,
        "resume_skills": sorted(resume_skills), "company_preparation": {
            "company_id": company.id if company else None, "company_name": company.name if company else None,
            "topics": company_topics, "message": "Company preparation topics are available." if company_topics else "No company-specific learning content is currently available."
        }}
