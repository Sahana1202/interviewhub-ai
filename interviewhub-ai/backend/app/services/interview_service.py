from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession, InterviewStatus
from app.models.resume import Resume
from app.models.company import Company
from app.schemas.interview import InterviewAnswerRequest, InterviewDetailRead, InterviewQuestionRead, InterviewSessionRead, InterviewStartRequest
from app.services.interview_engine import create_next_question, question_limit
from app.services.interviewers import INTERVIEWERS


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def remaining_seconds(session: InterviewSession, now: datetime | None = None) -> int:
    left = session.remaining_seconds
    if session.status == InterviewStatus.IN_PROGRESS and session.started_at:
        left -= int(((now or utc_now()) - as_utc(session.started_at)).total_seconds())
    return max(0, left)


def owned_session(db: Session, user_id: int, session_id: int) -> InterviewSession:
    query = select(InterviewSession).options(
        selectinload(InterviewSession.questions).selectinload(InterviewQuestion.answer),
        selectinload(InterviewSession.questions).selectinload(InterviewQuestion.answer).selectinload(InterviewAnswer.evaluation),
        selectinload(InterviewSession.resume),
    ).where(InterviewSession.id == session_id, InterviewSession.user_id == user_id)
    session = db.scalar(query)
    if session is None:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return session


def session_read(session: InterviewSession, now: datetime | None = None) -> InterviewSessionRead:
    data = {
        field: getattr(session, field)
        for field in (
            "id", "company_id", "company_name", "job_role", "experience_level", "interview_type", "difficulty", "resume_id",
            "duration_minutes", "interviewer_id", "advanced_interview_type", "difficulty_mode", "current_difficulty", "ai_enabled", "response_mode", "status", "current_question_index",
            "started_at", "paused_at", "completed_at", "created_at", "updated_at",
        )
    }
    data.update(
        interviewer_name=INTERVIEWERS[session.interviewer_id]["name"],
        resume_file_name=session.resume.file_name if session.resume else None,
        remaining_seconds=remaining_seconds(session, now),
        question_count=len(session.questions),
        answers_count=sum(question.answer is not None for question in session.questions),
        evaluations_count=sum(bool(question.answer and question.answer.evaluation) for question in session.questions),
        question_limit=question_limit(session),
    )
    return InterviewSessionRead.model_validate(data)


def detail_read(session: InterviewSession, now: datetime | None = None) -> InterviewDetailRead:
    data = session_read(session, now).model_dump()
    questions = []
    for question in session.questions:
        value = InterviewQuestionRead.model_validate(question).model_dump()
        if question.answer and question.answer.evaluation:
            evaluation = question.answer.evaluation
            value["evaluation"] = {
                "id": evaluation.id, "answer_id": evaluation.answer_id,
                "overall_feedback": evaluation.overall_feedback, "strengths": evaluation.strengths_json,
                "areas_to_improve": evaluation.improvements_json,
                "technical_accuracy": evaluation.technical_accuracy, "relevance": evaluation.relevance,
                "clarity": evaluation.clarity, "completeness": evaluation.completeness,
                "follow_up_needed": evaluation.follow_up_needed, "source": "ai_generated",
                "provider": evaluation.provider, "model": evaluation.model, "created_at": evaluation.created_at,
            }
        questions.append(value)
    data["questions"] = questions
    return InterviewDetailRead.model_validate(data)


def start_interview(db: Session, user_id: int, payload: InterviewStartRequest) -> tuple[InterviewSession, InterviewQuestion]:
    if payload.interviewer_id not in INTERVIEWERS or not INTERVIEWERS[payload.interviewer_id]["is_active"]:
        raise HTTPException(status_code=422, detail="Choose an active Virtual HR interviewer")
    if payload.resume_id is not None and db.scalar(select(Resume.id).where(Resume.id == payload.resume_id, Resume.user_id == user_id)) is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    company = None
    if payload.company_id is not None:
        company = db.scalar(select(Company).where(Company.id == payload.company_id, Company.status == "active"))
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")
    now = utc_now()
    session = InterviewSession(
        user_id=user_id,
        company_name=company.name if company else payload.company_name,
        company_id=company.id if company else None,
        job_role=payload.job_role,
        experience_level=payload.experience_level,
        interview_type=payload.interview_type,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        interviewer_id=payload.interviewer_id,
        response_mode=payload.response_mode,
        advanced_interview_type=payload.advanced_interview_type,
        difficulty_mode=payload.difficulty_mode,
        current_difficulty=payload.current_difficulty if payload.difficulty_mode == "fixed" else payload.difficulty.value,
        ai_enabled=payload.ai_enabled,
        resume_id=payload.resume_id,
        status=InterviewStatus.IN_PROGRESS,
        current_question_index=0,
        remaining_seconds=payload.duration_minutes * 60,
        started_at=now,
    )
    db.add(session)
    db.flush()
    question = create_next_question(db, session)
    if question is None:
        raise HTTPException(status_code=500, detail="A starter question could not be selected")
    db.commit()
    db.refresh(session)
    return owned_session(db, user_id, session.id), question


def list_interviews(db: Session, user_id: int) -> list[InterviewSessionRead]:
    sessions = db.scalars(
        select(InterviewSession).options(
            selectinload(InterviewSession.questions).selectinload(InterviewQuestion.answer),
        selectinload(InterviewSession.questions).selectinload(InterviewQuestion.answer).selectinload(InterviewAnswer.evaluation),
            selectinload(InterviewSession.resume),
        ).where(InterviewSession.user_id == user_id).order_by(InterviewSession.created_at.desc())
    ).all()
    return [session_read(session) for session in sessions]


def submit_answer(db: Session, user_id: int, session_id: int, payload: InterviewAnswerRequest):
    session = owned_session(db, user_id, session_id)
    if session.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Resume the interview before submitting an answer")
    question = next((item for item in session.questions if item.sequence_number == session.current_question_index), None)
    if question is None or question.id != payload.question_id:
        raise HTTPException(status_code=409, detail="This is not the current interview question")
    if question.answer is not None:
        raise HTTPException(status_code=409, detail="An answer has already been saved for this question")
    if payload.response_mode != session.response_mode:
        raise HTTPException(status_code=422, detail="Answer mode must match the interview setup")
    answer_text = payload.answer_text or payload.transcript or ""
    answer = InterviewAnswer(
        question_id=question.id,
        answer_text=answer_text,
        transcript=payload.transcript,
        response_mode=payload.response_mode,
        duration_seconds=payload.duration_seconds,
    )
    db.add(answer)
    db.flush()
    question.answer = answer
    next_question = None
    if remaining_seconds(session) > 0:
        next_question = create_next_question(db, session)
    else:
        session.remaining_seconds = 0
        session.status = InterviewStatus.COMPLETED
        session.started_at = None
        session.completed_at = utc_now()
    db.commit()
    db.refresh(session)
    refreshed = owned_session(db, user_id, session.id)
    saved = next(item for item in refreshed.questions if item.id == question.id).answer
    return refreshed, saved, next_question


def pause_or_resume(db: Session, user_id: int, session_id: int) -> InterviewSession:
    session = owned_session(db, user_id, session_id)
    now = utc_now()
    if session.status == InterviewStatus.IN_PROGRESS:
        left = remaining_seconds(session, now)
        session.remaining_seconds = left
        session.started_at = None
        session.paused_at = now
        session.status = InterviewStatus.PAUSED if left > 0 else InterviewStatus.COMPLETED
        if left == 0:
            session.completed_at = now
    elif session.status == InterviewStatus.PAUSED:
        session.started_at = now
        session.paused_at = None
        session.status = InterviewStatus.IN_PROGRESS
    else:
        raise HTTPException(status_code=409, detail="Only an active or paused interview can be paused or resumed")
    db.commit()
    return owned_session(db, user_id, session_id)


def complete_interview(db: Session, user_id: int, session_id: int) -> InterviewSession:
    session = owned_session(db, user_id, session_id)
    if session.status not in (InterviewStatus.IN_PROGRESS, InterviewStatus.PAUSED):
        if session.status == InterviewStatus.COMPLETED:
            return session
        raise HTTPException(status_code=409, detail="This interview cannot be completed")
    now = utc_now()
    session.remaining_seconds = remaining_seconds(session, now)
    session.status = InterviewStatus.COMPLETED
    session.started_at = None
    session.paused_at = None
    session.completed_at = now
    db.commit()
    return owned_session(db, user_id, session_id)
