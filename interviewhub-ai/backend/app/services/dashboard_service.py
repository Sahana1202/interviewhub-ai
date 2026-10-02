from app.models.user import User
from app.schemas.dashboard import DashboardActivity, DashboardProfile, DashboardProgress, DashboardResponse
from app.services.learning_service import progress_list, recommendations
from sqlalchemy.orm import Session

PROFILE_FIELDS = ("college", "degree", "department", "graduation_year", "experience_level", "target_role", "target_industry", "location")


def recommended_topics(role: str | None) -> list[str]:
    if not role or not role.strip():
        return []
    normalized = role.casefold()
    if any(term in normalized for term in ("python", "backend", "back-end", "full stack", "software engineer", "developer")):
        return ["Python fundamentals", "Object-oriented programming", "SQL and database basics", "REST API design", "Data structures", "Git and GitHub"]
    if any(term in normalized for term in ("ai", "machine learning", "data scientist", "data analyst", " ml ")):
        return ["Python fundamentals", "Statistics and probability", "NumPy and Pandas", "Machine learning basics", "SQL", "Data visualization"]
    return [f"Core skills for {role.strip()}", "Problem-solving practice", "Communication practice", "Role-specific interview questions"]


def build_dashboard(user: User, db: Session) -> DashboardResponse:
    profile = user.profile
    filled = sum(1 for field in PROFILE_FIELDS if getattr(profile, field) is not None and str(getattr(profile, field)).strip())
    completion = round(filled / len(PROFILE_FIELDS) * 100)
    role = profile.target_role
    return DashboardResponse(
        name=user.name,
        profile=DashboardProfile(target_role=role, target_industry=profile.target_industry, experience_level=profile.experience_level),
        profile_completion=completion,
        progress=DashboardProgress(),
        recommended_topics=recommended_topics(role),
        recent_activity=[],
        learning_progress=progress_list(db, user.id),
        recommended_learning=recommendations(db, user.id, role)["recommended_topics"],
    )
