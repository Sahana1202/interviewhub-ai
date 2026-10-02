"""Orchestrates validated provider calls and persists only bounded feedback."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.interview import (InterviewAnswer, InterviewEvaluation, InterviewQuestion,
                                  InterviewReport, InterviewSession, InterviewStatus)
from app.models.company import CompanyInterviewTopic
from app.models.learning import LearningTopic
from app.schemas.interview import EvaluationRead, ReportRead
from app.services.ai_service import AIProviderError, AIService, AIServiceUnavailable
from app.services.interview_context_builder import build_interview_context, evaluation_context, report_context


def _provider_or_503(service: AIService):
    if not service.available:
        raise HTTPException(status_code=503, detail="AI interview features unavailable. Please configure an AI provider.")


def _require_ai_enabled(session: InterviewSession):
    if not session.ai_enabled:
        raise HTTPException(status_code=409, detail="AI Interview Mode was not enabled for this session.")


def _provider_error(error: Exception):
    message = str(error) if isinstance(error, AIServiceUnavailable) else "AI evaluation is temporarily unavailable. Your answer has been saved. Please retry."
    raise HTTPException(status_code=503, detail=message)


def _question_for_session(db, session: InterviewSession):
    question = db.scalar(select(InterviewQuestion).where(InterviewQuestion.session_id == session.id,
        InterviewQuestion.sequence_number == session.current_question_index))
    if not question or question.answer:
        raise HTTPException(status_code=409, detail="There is no unanswered current question to update.")
    return question


def generate_question(db, user, session: InterviewSession, service: AIService):
    _require_ai_enabled(session)
    _provider_or_503(service)
    if session.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="AI questions are available only during an active interview.")
    question = _question_for_session(db, session)
    if question.question_source == "ai_generated":
        return question
    context = build_interview_context(db, user, session)
    try:
        generated = service.generate_question(context)
    except (AIServiceUnavailable, AIProviderError) as error:
        _provider_error(error)
    question.question_text = generated.question.strip()
    question.category = generated.category
    question.difficulty = session.current_difficulty
    question.question_source = "ai_generated"
    question.is_follow_up = False
    question.parent_question_id = None
    db.commit()
    db.refresh(question)
    return question


def _update_adaptive_difficulty(db, session: InterviewSession):
    if session.difficulty_mode != "adaptive":
        return
    evaluations = db.scalars(select(InterviewEvaluation).where(InterviewEvaluation.session_id == session.id)
        .order_by(InterviewEvaluation.created_at.desc()).limit(3)).all()
    if len(evaluations) < 2:
        return
    values = [getattr(item, field) for item in evaluations for field in ("technical_accuracy", "relevance", "clarity", "completeness") if getattr(item, field) is not None]
    if len(values) < 4:
        return
    average = sum(values) / len(values)
    levels = ["Beginner", "Intermediate", "Advanced"]
    current = session.current_difficulty if session.current_difficulty in levels else "Intermediate"
    position = levels.index(current)
    strong_signals = sum(
        not item.follow_up_needed and all((getattr(item, field) or 0) >= 7 for field in ("relevance", "clarity", "completeness"))
        and (item.technical_accuracy is None or item.technical_accuracy >= 7)
        for item in evaluations
    )
    needs_more_support = sum(item.follow_up_needed or any(
        getattr(item, field) is not None and getattr(item, field) < 5 for field in ("technical_accuracy", "relevance", "clarity", "completeness")
    ) for item in evaluations)
    # Require multiple recent signals; this is a practice pacing adjustment, not an ability judgment.
    if average >= 7.5 and strong_signals >= 2:
        position = min(len(levels) - 1, position + 1)
    elif average < 6.0 and needs_more_support >= 2:
        position = max(0, position - 1)
    session.current_difficulty = levels[position]
    db.commit()


def evaluate_answer(db, user, session: InterviewSession, answer_id: int, service: AIService):
    _require_ai_enabled(session)
    _provider_or_503(service)
    answer = db.scalar(select(InterviewAnswer).join(InterviewQuestion).where(
        InterviewAnswer.id == answer_id, InterviewQuestion.session_id == session.id))
    if answer is None:
        raise HTTPException(status_code=404, detail="Interview answer not found")
    existing = db.scalar(select(InterviewEvaluation).where(InterviewEvaluation.answer_id == answer.id))
    if existing:
        return evaluation_read(existing)
    question = db.scalar(select(InterviewQuestion).where(InterviewQuestion.id == answer.question_id))
    context = evaluation_context(db, user, session, question, answer)
    try:
        result = service.evaluate_answer(context)
    except (AIServiceUnavailable, AIProviderError) as error:
        _provider_error(error)
    record = InterviewEvaluation(
        session_id=session.id, answer_id=answer.id, overall_feedback=result.overall_feedback.strip(),
        strengths_json=[item.strip()[:300] for item in result.strengths if item.strip()][:6],
        improvements_json=[item.strip()[:300] for item in result.areas_to_improve if item.strip()][:6],
        technical_accuracy=result.technical_accuracy, relevance=result.relevance, clarity=result.clarity,
        completeness=result.completeness, follow_up_needed=result.follow_up_needed,
        provider=service.provider or "openai_compatible", model=service.model or "unknown",
    )
    db.add(record)
    db.flush()
    _update_adaptive_difficulty(db, session)
    db.commit()
    db.refresh(record)
    return evaluation_read(record)


def generate_followup(db, user, session: InterviewSession, answer_id: int, service: AIService):
    _require_ai_enabled(session)
    _provider_or_503(service)
    answer = db.scalar(select(InterviewAnswer).join(InterviewQuestion).where(
        InterviewAnswer.id == answer_id, InterviewQuestion.session_id == session.id))
    if answer is None:
        raise HTTPException(status_code=404, detail="Interview answer not found")
    parent = db.scalar(select(InterviewQuestion).where(InterviewQuestion.id == answer.question_id))
    evaluation = db.scalar(select(InterviewEvaluation).where(InterviewEvaluation.answer_id == answer.id))
    if not evaluation or not evaluation.follow_up_needed:
        raise HTTPException(status_code=409, detail="The saved evaluation did not recommend a follow-up.")
    root = parent
    if parent.is_follow_up and parent.parent_question_id:
        root = db.scalar(select(InterviewQuestion).where(InterviewQuestion.id == parent.parent_question_id)) or parent
    children = db.scalars(select(InterviewQuestion).where(InterviewQuestion.parent_question_id == root.id)).all()
    if len(children) >= 2:
        raise HTTPException(status_code=409, detail="This question has reached its contextual follow-up limit.")
    if session.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Follow-ups are available only during an active interview.")
    current = _question_for_session(db, session)
    context = evaluation_context(db, user, session, parent, answer)
    context["evaluation_feedback"] = evaluation.overall_feedback[:600]
    try:
        generated = service.generate_followup(context)
    except (AIServiceUnavailable, AIProviderError) as error:
        _provider_error(error)
    current.question_text = generated.question.strip()
    current.category = generated.category
    current.difficulty = session.current_difficulty
    current.question_source = "ai_generated"
    current.is_follow_up = True
    current.parent_question_id = root.id
    db.commit()
    db.refresh(current)
    return current


def generate_final_report(db, user, session: InterviewSession, service: AIService):
    _require_ai_enabled(session)
    _provider_or_503(service)
    if session.status != InterviewStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Complete the interview before generating its report.")
    existing = db.scalar(select(InterviewReport).where(InterviewReport.session_id == session.id))
    if existing:
        return report_read(existing)
    if not db.scalar(select(InterviewEvaluation.id).where(InterviewEvaluation.session_id == session.id).limit(1)):
        raise HTTPException(status_code=409, detail="Evaluate at least one saved answer before generating a practice report.")
    try:
        result = service.generate_report(report_context(db, user, session))
    except (AIServiceUnavailable, AIProviderError) as error:
        _provider_error(error)
    recommended = []
    topics = db.scalars(select(LearningTopic).where(LearningTopic.is_active.is_(True))).all()
    for recommendation in result.recommended_topics[:8]:
        recommended_slug = "-".join("".join(char for char in part if char.isalnum()) for part in recommendation.topic.casefold().split())
        match = next((item for item in topics if item.name.casefold() == recommendation.topic.casefold()
            or item.slug.casefold() == recommended_slug
            or recommended_slug.endswith(f"-{item.slug.casefold()}")), None)
        recommended.append({"topic": recommendation.topic, "reason": recommendation.reason,
            "topic_id": match.id if match else None, "href": f"/learning/topic/{match.id}" if match else None})
    if session.company_id:
        company_topics = db.scalars(select(CompanyInterviewTopic).where(
            CompanyInterviewTopic.company_id == session.company_id,
            CompanyInterviewTopic.verification_status.in_(["verified", "publicly_reported"])).limit(1)).all()
        if company_topics:
            recommended.append({"topic":"Company Knowledge Trainer", "reason":"Practice sourced public company information; this is not a guarantee of company interview procedure.", "topic_id":None, "href":f"/company/{session.company_id}/knowledge"})
    resume = session.resume
    projects = (resume.parsed_data or {}).get("projects", []) if resume and resume.status == "processed" else []
    for project in projects[:2]:
        if isinstance(project, dict) and project.get("name"):
            recommended.append({"topic":f"Practice explaining {str(project['name'])[:120]}", "reason":"Review architecture, technology choices, challenges, and results using only the details in your resume.", "topic_id":None, "href":None})
    topic_breakdown = [row.model_dump() for row in result.topic_breakdown[:20]]
    question_feedback = []
    rows = db.scalars(select(InterviewQuestion).options(selectinload(InterviewQuestion.answer).selectinload(InterviewAnswer.evaluation))
        .where(InterviewQuestion.session_id == session.id).order_by(InterviewQuestion.sequence_number)).all()
    for question in rows:
        if question.answer and question.answer.evaluation:
            ev = question.answer.evaluation
            question_feedback.append({"question":question.question_text[:500], "answer":question.answer.answer_text[:1000], "category":question.category.value,
                "feedback":ev.overall_feedback[:600], "strengths":ev.strengths_json[:4], "areas_to_improve":ev.improvements_json[:4], "source":"ai_generated"})
    record = InterviewReport(session_id=session.id, summary=result.summary.strip(),
        strengths_json=[item.strip()[:300] for item in result.strengths if item.strip()][:8],
        improvement_areas_json=[item.strip()[:300] for item in result.improvement_areas if item.strip()][:8],
        topic_breakdown_json=topic_breakdown, communication_feedback=result.communication_feedback.strip(),
        technical_feedback=result.technical_feedback.strip(), recommended_topics_json=recommended,
        question_feedback_json=question_feedback,
        provider=service.provider or "openai_compatible", model=service.model or "unknown")
    db.add(record)
    db.commit()
    db.refresh(record)
    return report_read(record)


def evaluation_read(record: InterviewEvaluation) -> EvaluationRead:
    return EvaluationRead(id=record.id, answer_id=record.answer_id, overall_feedback=record.overall_feedback,
        strengths=record.strengths_json, areas_to_improve=record.improvements_json,
        technical_accuracy=record.technical_accuracy, relevance=record.relevance, clarity=record.clarity,
        completeness=record.completeness, follow_up_needed=record.follow_up_needed,
        provider=record.provider, model=record.model, created_at=record.created_at)


def report_read(record: InterviewReport) -> ReportRead:
    return ReportRead(id=record.id, session_id=record.session_id, summary=record.summary,
        strengths=record.strengths_json, improvement_areas=record.improvement_areas_json,
        topic_breakdown=record.topic_breakdown_json, communication_feedback=record.communication_feedback,
        technical_feedback=record.technical_feedback, recommended_topics=record.recommended_topics_json,
        question_feedback=record.question_feedback_json or [],
        provider=record.provider, model=record.model, created_at=record.created_at)


def get_report(db, session: InterviewSession):
    record = db.scalar(select(InterviewReport).where(InterviewReport.session_id == session.id))
    if not record:
        raise HTTPException(status_code=404, detail="No AI-generated report is available for this interview.")
    return report_read(record)

