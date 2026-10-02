from datetime import date, datetime, time, timezone
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.admin import AdminActivityLog
from app.models.company import Company, CompanySource, CompanyTechnology, CompanyRole, CompanyInterviewTopic
from app.models.interview import InterviewSession
from app.models.learning import LearningCategory, LearningTopic, LearningResource, PracticeQuestion, PracticeAttempt, LearningProgress
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


def audit(db: Session, actor: User, action: str, entity: str, entity_id: int | None, metadata: dict[str, Any] | None = None) -> None:
    # Callers only pass allow-listed, non-sensitive values; never request bodies or content.
    db.add(AdminActivityLog(admin_user_id=actor.id, action=action, entity_type=entity,
                            entity_id=entity_id, safe_metadata=metadata or {}))


def safe_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL must be a valid HTTP or HTTPS URL without embedded credentials")
    return value.strip()


class CompanySourceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_type: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=2, max_length=240)
    url: str = Field(min_length=8, max_length=1000)
    publisher: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    verification_status: Literal["verified", "reported", "unverified"] = "unverified"

    @field_validator("url")
    @classmethod
    def validate_url(cls, value): return safe_url(value)


class CompanyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=200)
    industry: str | None = Field(default=None, max_length=160)
    founded_year: int | None = Field(default=None, ge=1800, le=2200)
    headquarters: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    status: Literal["active", "inactive"] = "active"
    source: CompanySourceIn

    @field_validator("website")
    @classmethod
    def validate_website(cls, value): return safe_url(value)


class CategoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(max_length=3000)
    icon: str = Field(default="book-open", max_length=50)
    display_order: int = Field(default=0, ge=0, le=10000)
    is_active: bool = True


class TopicIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(min_length=2, max_length=180, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str = Field(max_length=5000)
    difficulty: Literal["Easy", "Medium", "Hard"] = "Easy"
    content: dict[str, Any] = Field(default_factory=dict)
    estimated_minutes: int = Field(default=10, ge=1, le=600)
    display_order: int = Field(default=0, ge=0, le=10000)
    is_active: bool = True


class QuestionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic_id: int = Field(gt=0)
    question: str = Field(min_length=4, max_length=10000)
    question_type: Literal["mcq", "short_answer"] = "mcq"
    options: list[str] | None = None
    correct_answer: int | str | dict | None = None
    explanation: str = Field(default="", max_length=10000)
    difficulty: Literal["Easy", "Medium", "Hard"] = "Easy"
    is_active: bool = True

    @model_validator(mode="after")
    def validate_mcq(self):
        if self.question_type == "mcq":
            if not self.options or not 2 <= len(self.options) <= 10 or any(not o.strip() for o in self.options):
                raise ValueError("MCQ questions require 2 to 10 non-empty options")
            if not isinstance(self.correct_answer, int) or not 0 <= self.correct_answer < len(self.options):
                raise ValueError("Correct answer must be a valid option index")
        return self


class ResourceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=2, max_length=240)
    description: str = Field(default="", max_length=5000)
    category: str = Field(min_length=2, max_length=100)
    resource_type: str = Field(min_length=2, max_length=30)
    url: str | None = Field(default=None, max_length=1000)
    provider: str | None = Field(default=None, max_length=200)
    source: str = Field(default="admin", max_length=40)
    duration_minutes: int | None = Field(default=None, ge=1, le=10000)
    is_verified: bool = False
    is_active: bool = True

    @field_validator("url")
    @classmethod
    def validate_url(cls, value): return safe_url(value)


class SourceVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verification_status: Literal["verified", "reported", "unverified"]


class CompanyFactIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str = Field(min_length=1, max_length=500)
    source_id: int = Field(gt=0)
    category: str = Field(default="Other", max_length=60)


class CompanyRoleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role_title: str = Field(min_length=2, max_length=200)
    source_id: int = Field(gt=0)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=80)
    skills: list[str] = Field(default_factory=list, max_length=30)


class CompanyTopicIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=80)
    source_id: int = Field(gt=0)
    verification_status: Literal["verified", "reported", "unverified"] = "reported"


def page(query, db, offset, limit):
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    return total, db.scalars(query.offset(offset).limit(limit)).all()


def record_read(row):
    return {"id": row.id, "name": row.name, "email": row.email, "role": row.role,
            "is_active": row.is_active, "created_at": row.created_at,
            "profile": {"onboarding_completed": bool(row.profile and row.profile.onboarding_completed),
                        "target_role": row.profile.target_role if row.profile else None,
                        "target_industry": row.profile.target_industry if row.profile else None}}


@router.get("/dashboard")
def dashboard(date_from: date | None = None, date_to: date | None = None,
              actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from must not be after date_to")
    counts = {
        "users": db.scalar(select(func.count(User.id))) or 0,
        "active_users": db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0,
        "interview_sessions": db.scalar(select(func.count(InterviewSession.id))) or 0,
        "completed_interviews": db.scalar(select(func.count(InterviewSession.id)).where(InterviewSession.status == "completed")) or 0,
        "resumes": db.scalar(select(func.count(Resume.id))) or 0,
        "companies": db.scalar(select(func.count(Company.id)).where(Company.status == "active")) or 0,
        "learning_topics": db.scalar(select(func.count(LearningTopic.id)).where(LearningTopic.is_active.is_(True))) or 0,
        "practice_attempts": db.scalar(select(func.count(PracticeAttempt.id))) or 0,
    }
    def dated_series(model, field, where=None):
        col = getattr(model, field)
        stmt = select(func.date(col), func.count()).where(col.is_not(None))
        if date_from: stmt = stmt.where(col >= datetime.combine(date_from, time.min))
        if date_to: stmt = stmt.where(col < datetime.combine(date_to, time.max))
        if where is not None: stmt = stmt.where(where)
        return [{"date": str(d), "count": n} for d, n in db.execute(stmt.group_by(func.date(col)).order_by(func.date(col))).all()]
    interview_status = db.execute(select(InterviewSession.status, func.count()).group_by(InterviewSession.status)).all()
    practice_status = db.execute(select(PracticeAttempt.started_at, func.count()).group_by(func.date(PracticeAttempt.started_at)).order_by(func.date(PracticeAttempt.started_at))).all()
    progress = db.execute(select(func.date(LearningProgress.updated_at), func.count()).where(LearningProgress.completed.is_(True)).group_by(func.date(LearningProgress.updated_at)).order_by(func.date(LearningProgress.updated_at))).all()
    return {"stats": counts, "active_users_definition": "Accounts with is_active=true.",
            "registrations": dated_series(User, "created_at"),
            "interviews": dated_series(InterviewSession, "created_at"),
            "interview_status": [{"status": str(k.value if hasattr(k, 'value') else k), "count": v} for k, v in interview_status],
            "practice_activity": [{"date": str(d), "count": n} for d, n in practice_status],
            "topic_completions": [{"date": str(d), "count": n} for d, n in progress]}


@router.get("/users")
def users(search: str | None = None, role: Literal["admin", "candidate"] | None = None,
          active: bool | None = None, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100),
          actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    stmt = select(User).options(joinedload(User.profile))
    if search: stmt = stmt.where(or_(User.name.ilike(f"%{search.strip()}%"), User.email.ilike(f"%{search.strip()}%")))
    if role: stmt = stmt.where(User.role == role)
    if active is not None: stmt = stmt.where(User.is_active.is_(active))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(limit)).all()
    return {"users": [record_read(u) for u in rows], "total": total, "offset": offset, "limit": limit}


@router.get("/users/{user_id}")
def user_detail(user_id: int, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    user = db.scalar(select(User).options(joinedload(User.profile)).where(User.id == user_id))
    if not user: raise HTTPException(404, "User not found")
    return {**record_read(user),
            "interviews": {"total": db.scalar(select(func.count()).select_from(InterviewSession).where(InterviewSession.user_id == user_id)) or 0,
                           "completed": db.scalar(select(func.count()).select_from(InterviewSession).where(InterviewSession.user_id == user_id, InterviewSession.status == "completed")) or 0},
            "resumes_count": db.scalar(select(func.count()).select_from(Resume).where(Resume.user_id == user_id)) or 0,
            "practice_attempts": db.scalar(select(func.count()).select_from(PracticeAttempt).where(PracticeAttempt.user_id == user_id)) or 0,
            "completed_topics": db.scalar(select(func.count()).select_from(LearningProgress).where(LearningProgress.user_id == user_id, LearningProgress.completed.is_(True))) or 0}


@router.patch("/users/{user_id}/status")
def user_status(user_id: int, is_active: bool, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    if user.role == "admin" and user.is_active and not is_active:
        remaining = db.scalar(select(func.count(User.id)).where(User.role == "admin", User.is_active.is_(True))) or 0
        if remaining <= 1: raise HTTPException(409, "The last active administrator cannot be deactivated")
    old = user.is_active; user.is_active = is_active
    audit(db, actor, "user.status_changed", "user", user.id, {"from": old, "to": is_active})
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


class RoleChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["candidate", "admin"]


@router.patch("/users/{user_id}/role")
def user_role(user_id: int, payload: RoleChange, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    if user.id == actor.id and payload.role != "admin": raise HTTPException(409, "You cannot demote your own administrator account")
    if user.role == "admin" and payload.role != "admin":
        count = db.scalar(select(func.count(User.id)).where(User.role == "admin", User.is_active.is_(True))) or 0
        if user.is_active and count <= 1: raise HTTPException(409, "The last active administrator cannot be demoted")
    old = user.role; user.role = payload.role
    audit(db, actor, "user.role_changed", "user", user.id, {"from": old, "to": payload.role})
    db.commit()
    return {"id": user.id, "role": user.role}


def company_read(c):
    return {"id": c.id, "name": c.name, "industry": c.industry, "founded_year": c.founded_year,
            "headquarters": c.headquarters, "website": c.website, "description": c.description, "status": c.status,
            "sources": [{"id": s.id, "title": s.title, "url": s.url, "source_type": s.source_type,
                         "publisher": s.publisher, "verification_status": s.verification_status,
                         "retrieved_at": s.retrieved_at} for s in c.sources],
            "technology_count": len(c.technologies), "role_count": len(c.roles), "topic_count": len(c.topics)}


@router.get("/companies")
def company_list(search: str | None = None, offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100),
                 actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    stmt = select(Company).options(joinedload(Company.sources), joinedload(Company.technologies), joinedload(Company.roles), joinedload(Company.topics))
    if search: stmt = stmt.where(Company.name.ilike(f"%{search.strip()}%"))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.scalars(stmt.order_by(Company.name).offset(offset).limit(limit)).unique().all()
    return {"companies": [company_read(c) for c in rows], "total": total, "offset": offset, "limit": limit}


@router.post("/companies", status_code=201)
def company_create(payload: CompanyIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    company = Company(name=payload.name.strip(), normalized_name=payload.name.strip().casefold(), industry=payload.industry,
                      founded_year=payload.founded_year, headquarters=payload.headquarters, website=payload.website,
                      description=payload.description, status=payload.status)
    company.sources.append(CompanySource(**payload.source.model_dump(), retrieved_at=datetime.now(timezone.utc)))
    db.add(company)
    try:
        db.flush(); audit(db, actor, "company.created", "company", company.id, {"name": company.name}); db.commit(); db.refresh(company)
    except Exception:
        db.rollback(); raise HTTPException(409, "Company could not be created; check for a duplicate name") from None
    return company_read(company)


@router.patch("/companies/{company_id}")
def company_update(company_id: int, payload: CompanyIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.get(Company, company_id)
    if not c: raise HTTPException(404, "Company not found")
    for key in ("name", "industry", "founded_year", "headquarters", "website", "description", "status"):
        value = getattr(payload, key)
        setattr(c, key, value.strip() if key == "name" else value)
    c.normalized_name = c.name.casefold()
    c.sources.append(CompanySource(**payload.source.model_dump(), retrieved_at=datetime.now(timezone.utc)))
    audit(db, actor, "company.updated", "company", c.id, {"name": c.name, "source_added": True})
    try: db.commit()
    except Exception: db.rollback(); raise HTTPException(409, "Company update conflicts with an existing record") from None
    return company_read(c)


@router.delete("/companies/{company_id}")
def company_deactivate(company_id: int, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.get(Company, company_id)
    if not c: raise HTTPException(404, "Company not found")
    c.status = "inactive"; audit(db, actor, "company.deactivated", "company", c.id); db.commit()
    return {"id": c.id, "status": c.status}


@router.patch("/companies/sources/{source_id}/verification")
def source_verification(source_id: int, payload: SourceVerification, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    source = db.get(CompanySource, source_id)
    if not source: raise HTTPException(404, "Company source not found")
    source.verification_status = payload.verification_status
    source.retrieved_at = datetime.now(timezone.utc)
    audit(db, actor, "company.source_verified", "company_source", source.id, {"verification_status": source.verification_status})
    db.commit()
    return {"id": source.id, "verification_status": source.verification_status, "retrieved_at": source.retrieved_at}


@router.post("/companies/{company_id}/technologies", status_code=201)
def company_technology(company_id: int, payload: CompanyFactIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not db.get(Company, company_id): raise HTTPException(404, "Company not found")
    source = db.get(CompanySource, payload.source_id)
    if not source or source.company_id != company_id: raise HTTPException(422, "Source must belong to this company")
    row = CompanyTechnology(company_id=company_id, technology=payload.value, category=payload.category, source_id=source.id)
    db.add(row); db.flush(); audit(db, actor, "company.technology_added", "company_technology", row.id, {"source_id": source.id}); db.commit()
    return {"id": row.id, "technology": row.technology}


@router.post("/companies/{company_id}/roles", status_code=201)
def company_role(company_id: int, payload: CompanyRoleIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not db.get(Company, company_id): raise HTTPException(404, "Company not found")
    source = db.get(CompanySource, payload.source_id)
    if not source or source.company_id != company_id: raise HTTPException(422, "Source must belong to this company")
    row = CompanyRole(company_id=company_id, source_id=source.id, role_title=payload.role_title,
                      location=payload.location, employment_type=payload.employment_type, skills=payload.skills)
    db.add(row); db.flush(); audit(db, actor, "company.role_added", "company_role", row.id, {"source_id": source.id}); db.commit()
    return {"id": row.id, "role_title": row.role_title}


@router.post("/companies/{company_id}/topics", status_code=201)
def company_topic(company_id: int, payload: CompanyTopicIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not db.get(Company, company_id): raise HTTPException(404, "Company not found")
    source = db.get(CompanySource, payload.source_id)
    if not source or source.company_id != company_id: raise HTTPException(422, "Source must belong to this company")
    row = CompanyInterviewTopic(company_id=company_id, source_id=source.id, topic=payload.topic,
                                category=payload.category, verification_status=payload.verification_status)
    db.add(row); db.flush(); audit(db, actor, "company.reported_topic_added", "company_interview_topic", row.id, {"verification_status": row.verification_status}); db.commit()
    return {"id": row.id, "topic": row.topic, "label": "Reported interview experience; not guaranteed"}


@router.delete("/companies/{company_id}/topics/{topic_id}")
def company_topic_remove(company_id: int, topic_id: int, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.get(CompanyInterviewTopic, topic_id)
    if not row or row.company_id != company_id: raise HTTPException(404, "Company topic not found")
    db.delete(row); audit(db, actor, "company.topic_removed", "company_interview_topic", topic_id); db.commit()
    return {"id": topic_id, "removed": True}


@router.get("/learning/topics")
def topic_list(offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    stmt = select(LearningTopic).order_by(LearningTopic.display_order, LearningTopic.name)
    total = db.scalar(select(func.count(LearningTopic.id))) or 0
    return {"topics": [{"id": t.id, "category_id": t.category_id, "name": t.name, "slug": t.slug, "description": t.description,
                        "difficulty": t.difficulty, "content": t.content, "estimated_minutes": t.estimated_minutes,
                        "display_order": t.display_order, "is_active": t.is_active,
                        "question_count": db.scalar(select(func.count(PracticeQuestion.id)).where(PracticeQuestion.topic_id == t.id)) or 0}
                       for t in db.scalars(stmt.offset(offset).limit(limit)).all()], "total": total, "offset": offset, "limit": limit}


@router.get("/learning/categories")
def category_list(actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    return {"categories": [{"id": c.id, "name": c.name, "slug": c.slug, "description": c.description,
                            "icon": c.icon, "display_order": c.display_order, "is_active": c.is_active}
                           for c in db.scalars(select(LearningCategory).order_by(LearningCategory.display_order)).all()]}


@router.post("/learning/categories", status_code=201)
def category_create(payload: CategoryIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    c = LearningCategory(**payload.model_dump()); db.add(c); db.flush(); audit(db, actor, "learning.category_created", "learning_category", c.id); db.commit()
    return {"id": c.id, "name": c.name, "slug": c.slug}


@router.post("/learning/topics", status_code=201)
def topic_create(payload: TopicIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not db.get(LearningCategory, payload.category_id): raise HTTPException(404, "Learning category not found")
    t = LearningTopic(**payload.model_dump()); db.add(t)
    try: db.flush(); audit(db, actor, "learning.topic_created", "learning_topic", t.id); db.commit()
    except Exception: db.rollback(); raise HTTPException(409, "Topic could not be created; check its category and slug") from None
    return {"id": t.id, "name": t.name, "is_active": t.is_active}


@router.patch("/learning/topics/{topic_id}")
def topic_update(topic_id: int, payload: TopicIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    t = db.get(LearningTopic, topic_id)
    if not t: raise HTTPException(404, "Learning topic not found")
    if not db.get(LearningCategory, payload.category_id): raise HTTPException(404, "Learning category not found")
    for key, value in payload.model_dump().items(): setattr(t, key, value)
    audit(db, actor, "learning.topic_updated", "learning_topic", t.id, {"is_active": t.is_active})
    try: db.commit()
    except Exception: db.rollback(); raise HTTPException(409, "Topic update conflicts with an existing record") from None
    return {"id": t.id, "name": t.name, "is_active": t.is_active}


@router.delete("/learning/topics/{topic_id}")
def topic_deactivate(topic_id: int, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    t = db.get(LearningTopic, topic_id)
    if not t: raise HTTPException(404, "Learning topic not found")
    t.is_active = False; audit(db, actor, "learning.topic_unpublished", "learning_topic", t.id); db.commit()
    return {"id": t.id, "is_active": False}


@router.get("/learning/questions")
def question_list(topic_id: int | None = Query(None, gt=0), offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    stmt = select(PracticeQuestion)
    if topic_id: stmt = stmt.where(PracticeQuestion.topic_id == topic_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    qs = db.scalars(stmt.order_by(PracticeQuestion.id.desc()).offset(offset).limit(limit)).all()
    return {"questions": [{"id": q.id, "topic_id": q.topic_id, "question": q.question, "question_type": q.question_type,
                           "options": q.options, "correct_answer": q.correct_answer, "explanation": q.explanation,
                           "difficulty": q.difficulty, "is_active": q.is_active} for q in qs], "total": total, "offset": offset, "limit": limit}


@router.post("/learning/questions", status_code=201)
def question_create(payload: QuestionIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    if not db.get(LearningTopic, payload.topic_id): raise HTTPException(404, "Learning topic not found")
    q = PracticeQuestion(**payload.model_dump()); db.add(q); db.flush(); audit(db, actor, "learning.question_created", "practice_question", q.id); db.commit()
    return {"id": q.id, "is_active": q.is_active}


@router.patch("/learning/questions/{question_id}")
def question_update(question_id: int, payload: QuestionIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.get(PracticeQuestion, question_id)
    if not q: raise HTTPException(404, "Practice question not found")
    if not db.get(LearningTopic, payload.topic_id): raise HTTPException(404, "Learning topic not found")
    for key, value in payload.model_dump().items(): setattr(q, key, value)
    audit(db, actor, "learning.question_updated", "practice_question", q.id); db.commit()
    return {"id": q.id, "is_active": q.is_active}


@router.delete("/learning/questions/{question_id}")
def question_deactivate(question_id: int, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.get(PracticeQuestion, question_id)
    if not q: raise HTTPException(404, "Practice question not found")
    q.is_active = False; audit(db, actor, "learning.question_unpublished", "practice_question", q.id); db.commit()
    return {"id": q.id, "is_active": False}


@router.get("/resources")
def resource_list(offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    stmt = select(LearningResource).where(LearningResource.user_id.is_(None)).order_by(LearningResource.updated_at.desc())
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rs = db.scalars(stmt.offset(offset).limit(limit)).all()
    return {"resources": [{"id": r.id, "topic_id": r.topic_id, "title": r.title, "description": r.description,
                           "category": r.category, "resource_type": r.resource_type, "url": r.url, "provider": r.provider,
                           "source": r.source, "duration_minutes": r.duration_minutes, "is_verified": r.is_verified,
                           "is_active": r.is_active, "created_at": r.created_at, "updated_at": r.updated_at} for r in rs],
            "total": total, "offset": offset, "limit": limit}


@router.post("/resources", status_code=201)
def resource_create(payload: ResourceIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    if payload.topic_id and not db.get(LearningTopic, payload.topic_id): raise HTTPException(404, "Learning topic not found")
    r = LearningResource(**payload.model_dump(), user_id=None); db.add(r); db.flush(); audit(db, actor, "resource.created", "learning_resource", r.id); db.commit()
    return {"id": r.id, "title": r.title, "is_active": r.is_active}


@router.patch("/resources/{resource_id}")
def resource_update(resource_id: int, payload: ResourceIn, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.get(LearningResource, resource_id)
    if not r or r.user_id is not None: raise HTTPException(404, "Platform resource not found")
    if payload.topic_id and not db.get(LearningTopic, payload.topic_id): raise HTTPException(404, "Learning topic not found")
    for key, value in payload.model_dump().items(): setattr(r, key, value)
    audit(db, actor, "resource.updated", "learning_resource", r.id); db.commit()
    return {"id": r.id, "title": r.title, "is_active": r.is_active}


@router.delete("/resources/{resource_id}")
def resource_deactivate(resource_id: int, actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.get(LearningResource, resource_id)
    if not r or r.user_id is not None: raise HTTPException(404, "Platform resource not found")
    r.is_active = False; audit(db, actor, "resource.unpublished", "learning_resource", r.id); db.commit()
    return {"id": r.id, "is_active": False}


@router.get("/interviews/analytics")
def interview_analytics(date_from: date | None = None, date_to: date | None = None,
                        interview_type: Literal["HR", "Technical", "Combined"] | None = None,
                        actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    stmt = select(InterviewSession)
    if date_from: stmt = stmt.where(InterviewSession.created_at >= datetime.combine(date_from, time.min))
    if date_to: stmt = stmt.where(InterviewSession.created_at < datetime.combine(date_to, time.max))
    if interview_type: stmt = stmt.where(InterviewSession.interview_type == interview_type)
    base = stmt.subquery()
    return {"total": db.scalar(select(func.count()).select_from(base)) or 0,
            "completed": db.scalar(select(func.count()).select_from(base).where(base.c.status == "completed")) or 0,
            "incomplete": db.scalar(select(func.count()).select_from(base).where(base.c.status != "completed")) or 0,
            "by_type": [{"type": str(t.value if hasattr(t, 'value') else t), "count": n} for t,n in db.execute(select(base.c.interview_type,func.count()).group_by(base.c.interview_type)).all()],
            "by_interviewer": [{"interviewer": name, "count": n} for name,n in db.execute(select(base.c.interviewer_id,func.count()).group_by(base.c.interviewer_id)).all()],
            "ai_enabled": db.scalar(select(func.count()).select_from(base).where(base.c.ai_enabled.is_(True))) or 0,
            "rule_based": db.scalar(select(func.count()).select_from(base).where(base.c.ai_enabled.is_(False))) or 0,
            "privacy": "Aggregate counts only; candidate answers and evaluation text are not returned."}


@router.get("/activity-logs")
def activity_logs(admin_id: int | None = Query(None, gt=0), action: str | None = None, entity_type: str | None = None,
                  date_from: date | None = None, date_to: date | None = None,
                  offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100),
                  actor: User = Depends(require_admin), db: Session = Depends(get_db)):
    del actor
    if date_from and date_to and date_from > date_to: raise HTTPException(422, "date_from must not be after date_to")
    stmt = select(AdminActivityLog)
    if admin_id: stmt = stmt.where(AdminActivityLog.admin_user_id == admin_id)
    if action: stmt = stmt.where(AdminActivityLog.action == action)
    if entity_type: stmt = stmt.where(AdminActivityLog.entity_type == entity_type)
    if date_from: stmt = stmt.where(AdminActivityLog.created_at >= datetime.combine(date_from, time.min))
    if date_to: stmt = stmt.where(AdminActivityLog.created_at < datetime.combine(date_to, time.max))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(AdminActivityLog.created_at.desc(), AdminActivityLog.id.desc()).offset(offset).limit(limit)).all()
    return {"logs": [{"id": x.id, "admin_user_id": x.admin_user_id, "action": x.action, "entity_type": x.entity_type,
                      "entity_id": x.entity_id, "metadata": x.safe_metadata, "created_at": x.created_at} for x in rows],
            "total": total, "offset": offset, "limit": limit}
