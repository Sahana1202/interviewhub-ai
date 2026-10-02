import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import (Company, CompanySource, CompanyTechnology, CompanyRole,
    CompanyInterviewReport, CompanyInterviewTopic, CompanyQuizQuestion, CompanyQuizAttempt,
    UserCompanyBookmark)


def normalize_name(name: str) -> str:
    value = unicodedata.normalize("NFKC", name).casefold().strip()
    return re.sub(r"\s+", " ", value)


def safe_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not parsed.username and not parsed.password


def ingest_company(db: Session, *, name: str, source: dict, facts: dict | None = None) -> Company:
    """Controlled ingestion helper for trusted operators/providers; intentionally not an HTTP API."""
    cleaned = " ".join(name.split())
    allowed_source_types = {"official_website", "official_careers", "official_document", "official_news", "reputable_news", "job_listing", "public_interview_report", "other_public_source"}
    if (not cleaned or len(cleaned) > 200 or not safe_url(source.get("url", ""))
            or source.get("source_type") not in allowed_source_types or not source.get("title", "").strip()):
        raise ValueError("A company name and valid HTTP(S) source URL are required")
    status = source.get("verification_status", "needs_verification")
    if status not in {"verified", "publicly_reported", "needs_verification", "unavailable"}:
        raise ValueError("Invalid source verification status")
    company = db.scalar(select(Company).where(Company.normalized_name == normalize_name(cleaned)))
    if company is None:
        company = Company(name=cleaned, normalized_name=normalize_name(cleaned))
        db.add(company)
        db.flush()
    facts = facts or {}
    for key in ("website", "logo_url"):
        if facts.get(key) is not None and not safe_url(facts[key]):
            raise ValueError(f"{key} must use a valid HTTP(S) URL")
    for key in ("industry", "headquarters", "website", "description", "logo_url"):
        if key in facts:
            setattr(company, key, facts[key])
    if "founded_year" in facts:
        company.founded_year = facts["founded_year"]
    db.add(CompanySource(company_id=company.id, source_type=source["source_type"], title=source["title"],
        url=source["url"], publisher=source.get("publisher"), published_at=source.get("published_at"),
        retrieved_at=source.get("retrieved_at") or datetime.now(timezone.utc),
        verification_status=status, summary=source.get("summary")))
    db.flush()
    source_row = db.scalar(select(CompanySource).where(CompanySource.company_id == company.id).order_by(CompanySource.id.desc()))
    for item in facts.get("technologies", []):
        if not item.get("technology"):
            raise ValueError("Technology entries require a name")
        db.add(CompanyTechnology(company_id=company.id, technology=item["technology"],
            category=item.get("category", "Other"), source_id=source_row.id,
            confidence=item.get("confidence", "documented")))
    for item in facts.get("roles", []):
        if not item.get("role_title") or item.get("status", "unknown") not in {"current", "historical", "reported", "unknown"}:
            raise ValueError("Role entries require a title and valid freshness status")
        db.add(CompanyRole(company_id=company.id, role_title=item["role_title"], location=item.get("location"),
            employment_type=item.get("employment_type"), skills=item.get("skills", []), source_id=source_row.id,
            posted_at=item.get("posted_at"), expires_at=item.get("expires_at"), status=item.get("status", "unknown")))
    for item in facts.get("interview_reports", []):
        if not item.get("process_summary"):
            raise ValueError("Interview report entries require a summary")
        db.add(CompanyInterviewReport(company_id=company.id, role=item.get("role"),
            experience_level=item.get("experience_level"), process_summary=item["process_summary"],
            source_id=source_row.id, verification_status=item.get("verification_status", status)))
    for item in facts.get("interview_topics", []):
        if not item.get("topic"):
            raise ValueError("Interview topic entries require a topic")
        db.add(CompanyInterviewTopic(company_id=company.id, topic=item["topic"],
            category=item.get("category", "Other"), source_id=source_row.id,
            verification_status=item.get("verification_status", status)))
    db.commit()
    db.refresh(company)
    return company


def company_or_404(db: Session, company_id: int) -> Company:
    company = db.get(Company, company_id)
    if company is None or company.status != "active":
        raise HTTPException(status_code=404, detail="Company not found")
    return company


def search_companies(db: Session, q: str | None, offset: int, limit: int):
    query = select(Company).where(Company.status == "active")
    if q and q.strip():
        needle = normalize_name(q)
        query = query.where(Company.normalized_name.contains(needle))
    return db.scalars(query.order_by(Company.normalized_name).offset(offset).limit(limit)).all()


def company_detail(db: Session, company_id: int):
    company = company_or_404(db, company_id)
    sources = db.scalars(select(CompanySource).where(CompanySource.company_id == company_id).order_by(CompanySource.id)).all()
    source_map = {item.id: item for item in sources}
    def with_source(items):
        rows = []
        for item in items:
            data = {key: getattr(item, key) for key in item.__table__.columns.keys() if key not in {"company_id"}}
            source = source_map.get(getattr(item, "source_id", None))
            data["source"] = source_read(source) if source else None
            rows.append(data)
        return rows
    return {"company": company_read(company), "sources": [source_read(s) for s in sources],
        "technologies": with_source(db.scalars(select(CompanyTechnology).where(CompanyTechnology.company_id == company_id)).all()),
        "roles": with_source(db.scalars(select(CompanyRole).where(CompanyRole.company_id == company_id)).all()),
        "interview_insights": with_source(db.scalars(select(CompanyInterviewReport).where(CompanyInterviewReport.company_id == company_id)).all()),
        "interview_topics": with_source(db.scalars(select(CompanyInterviewTopic).where(CompanyInterviewTopic.company_id == company_id)).all())}


def company_read(company: Company):
    return {key: getattr(company, key) for key in ("id", "name", "industry", "founded_year", "headquarters", "website", "description", "logo_url", "status", "created_at", "updated_at")}


def source_read(source: CompanySource):
    return {key: getattr(source, key) for key in ("id", "source_type", "title", "url", "publisher", "published_at", "retrieved_at", "verification_status", "summary")}


def toggle_bookmark(db: Session, user_id: int, company_id: int, save: bool):
    company_or_404(db, company_id)
    record = db.scalar(select(UserCompanyBookmark).where(UserCompanyBookmark.user_id == user_id, UserCompanyBookmark.company_id == company_id))
    if save and record is None:
        db.add(UserCompanyBookmark(user_id=user_id, company_id=company_id))
    elif not save and record is not None:
        db.delete(record)
    db.commit()


def bookmarks(db: Session, user_id: int):
    return db.scalars(select(Company).join(UserCompanyBookmark).where(UserCompanyBookmark.user_id == user_id).order_by(Company.name)).all()


def interview_context(db: Session, company_id: int):
    info = company_detail(db, company_id)
    sources = info["sources"]
    return {"company_name": info["company"]["name"], "overview": info["company"]["description"],
        "technologies": info["technologies"], "roles": info["roles"], "reported_interview_topics": [t for t in info["interview_topics"] if t["category"].lower() != "hr"],
        "reported_hr_topics": [t for t in info["interview_topics"] if t["category"].lower() == "hr"], "sources": sources,
        "verification_notes": "Each item retains its source and verification status; no company-specific interview generation is enabled."}


def quiz_question(db: Session, company_id: int):
    company = company_or_404(db, company_id)
    # Only issue questions from verified source-backed company facts.
    question = db.scalar(select(CompanyQuizQuestion).join(CompanySource, CompanySource.id == CompanyQuizQuestion.source_id).where(
        CompanyQuizQuestion.company_id == company_id, CompanySource.verification_status == "verified").order_by(CompanyQuizQuestion.id))
    if question:
        return question
    source = db.scalar(select(CompanySource).where(CompanySource.company_id == company_id, CompanySource.verification_status == "verified").order_by(CompanySource.id))
    if not source or not company.founded_year:
        raise HTTPException(status_code=404, detail="No verified company facts are available for practice yet.")
    answer = company.founded_year
    options = [answer - 2, answer - 1, answer, answer + 1]
    # Deterministic rotation avoids making the correct option position constant.
    correct = 2
    question = CompanyQuizQuestion(company_id=company_id, question=f"According to {source.title}, in which year was {company.name} founded?",
        options=[str(year) for year in options], correct_answer=correct,
        explanation=f"The verified company record lists {answer}.", source_id=source.id)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def submit_quiz_answer(db: Session, user_id: int, company_id: int, question_id: int, selected: int):
    question = db.scalar(select(CompanyQuizQuestion).where(CompanyQuizQuestion.id == question_id, CompanyQuizQuestion.company_id == company_id))
    if question is None:
        raise HTTPException(status_code=404, detail="Practice question not found")
    if selected < 0 or selected >= len(question.options):
        raise HTTPException(status_code=422, detail="Select one of the available answers")
    correct = selected == question.correct_answer
    db.add(CompanyQuizAttempt(user_id=user_id, company_id=company_id, question_id=question_id, selected_answer=selected, correct=correct))
    db.commit()
    attempts = db.scalars(select(CompanyQuizAttempt).where(CompanyQuizAttempt.user_id == user_id, CompanyQuizAttempt.company_id == company_id)).all()
    return {"correct": correct, "selected_answer": selected, "correct_answer": question.correct_answer,
        "explanation": question.explanation, "attempted": len(attempts), "correct_count": sum(item.correct for item in attempts),
        "incorrect_count": sum(not item.correct for item in attempts), "completion_percent": 100 if attempts else 0}
