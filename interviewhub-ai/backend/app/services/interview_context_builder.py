"""Build small, relevant, user-owned interview context for provider calls."""
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.interview import InterviewAnswer, InterviewEvaluation, InterviewQuestion
from app.models.learning import LearningProgress, LearningTopic, PracticeAttempt
from app.services.company_context_builder import build_company_context
from app.services.resume_context_builder import build_resume_context
from app.services.interviewers import INTERVIEWERS

MAX_ANSWER_CHARS = 4000


def _profile_context(db, user_id: int) -> dict:
    from app.models.profile import UserProfile
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if not profile:
        return {}
    return {key: getattr(profile, key) for key in ("experience_level", "target_role", "target_industry", "degree", "department") if getattr(profile, key)}


def _learning_context(db, user_id: int) -> list[dict]:
    progress_rows = db.scalars(select(LearningProgress).where(LearningProgress.user_id == user_id)
        .order_by(LearningProgress.last_practiced_at.desc()).limit(12)).all()
    attempts = db.scalars(select(PracticeAttempt).where(PracticeAttempt.user_id == user_id, PracticeAttempt.status == "completed").order_by(PracticeAttempt.completed_at.desc()).limit(12)).all()
    topic_ids = {row.topic_id for row in [*progress_rows, *attempts]}
    topics = {row.id: row.name for row in db.scalars(select(LearningTopic).where(LearningTopic.id.in_(topic_ids))).all()} if topic_ids else {}
    grouped = {}
    for row in progress_rows:
        grouped[row.topic_id] = {"topic": topics.get(row.topic_id, "Practice topic"),
            "progress_percent": row.progress_percent, "completed": row.completed, "recent_accuracy": []}
    for row in attempts:
        record = grouped.setdefault(row.topic_id, {"topic": topics.get(row.topic_id, "Practice topic"),
            "progress_percent": 0, "completed": False, "recent_accuracy": []})
        if len(record["recent_accuracy"]) < 5:
            record["recent_accuracy"].append(round(row.accuracy, 1))
    return list(grouped.values())[:8]


def build_interview_context(db, user, session, *, answer=None, include_history=True) -> dict:
    questions = db.scalars(select(InterviewQuestion).options(selectinload(InterviewQuestion.answer).selectinload(InterviewAnswer.evaluation)).where(InterviewQuestion.session_id == session.id).order_by(InterviewQuestion.sequence_number.desc()).limit(8)).all()
    history = []
    if include_history:
        for row in reversed(questions):
            evaluation = row.answer.evaluation if row.answer else None
            history.append({"question": row.question_text[:500], "answer": (row.answer.answer_text[:MAX_ANSWER_CHARS] if row.answer else None),
                "category": row.category.value,
                "evaluation_signals": ({"strengths": evaluation.strengths_json[:3], "areas_to_improve": evaluation.improvements_json[:3], "follow_up_needed": evaluation.follow_up_needed} if evaluation else None)})
    resume = session.resume if session.resume_id else None
    company = session.company if session.company_id else None
    profile = _profile_context(db, user.id)
    persona = INTERVIEWERS.get(session.interviewer_id, {})
    return {
        "role": session.job_role,
        "company_label": session.company_name,
        "current_interview_state": {"question_number": session.current_question_index,
            "duration_minutes": session.duration_minutes, "status": session.status.value},
        "virtual_hr_persona": {"name": persona.get("name"), "style": persona.get("style", [])[:4]},
        "experience_level": session.experience_level or (profile or {}).get("experience_level"),
        "interview_type": session.advanced_interview_type,
        "difficulty": getattr(session, "current_difficulty", None) or session.difficulty.value,
        "difficulty_mode": session.difficulty_mode,
        "profile_context": profile,
        "resume_context": build_resume_context(resume),
        "company_context": build_company_context(db, company),
        "learning_context": _learning_context(db, user.id),
        "recent_interview_history": history,
        "submitted_answer": answer[:MAX_ANSWER_CHARS] if answer else None,
    }


def evaluation_context(db, user, session, question, answer) -> dict:
    context = build_interview_context(db, user, session, answer=answer.answer_text, include_history=True)
    context["current_question"] = question.question_text[:1200]
    return context


def report_context(db, user, session) -> dict:
    questions = db.scalars(select(InterviewQuestion).options(selectinload(InterviewQuestion.answer)).where(InterviewQuestion.session_id == session.id).order_by(InterviewQuestion.sequence_number)).all()
    evidence = []
    for question in questions:
        answer = question.answer
        if not answer:
            continue
        evaluation = db.scalar(select(InterviewEvaluation).where(InterviewEvaluation.answer_id == answer.id))
        if evaluation:
            evidence.append({"question": question.question_text[:500], "category": question.category.value,
                             "answer": answer.answer_text[:1000],
                             "evaluation": {"feedback": evaluation.overall_feedback[:400], "strengths": evaluation.strengths_json[:3], "areas_to_improve": evaluation.improvements_json[:3]}})
    context = build_interview_context(db, user, session, include_history=False)
    context["evidence"] = evidence[:8]
    return context
