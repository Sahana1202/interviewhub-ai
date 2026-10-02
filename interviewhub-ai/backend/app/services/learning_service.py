import random
from datetime import datetime, timezone, date, time
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.learning import (
    LearningCategory, LearningTopic, LearningResource, PracticeQuestion,
    PracticeAttempt, PracticeAttemptAnswer, LearningProgress,
)
from app.services.learning_recommendation_service import build_recommendations


def utc_now():
    return datetime.now(timezone.utc)


def not_found(message):
    raise HTTPException(status_code=404, detail=message)


def category_or_404(db: Session, category_id: int):
    item = db.scalar(select(LearningCategory).where(LearningCategory.id == category_id, LearningCategory.is_active.is_(True)))
    if item is None:
        not_found("Learning category not found")
    return item


def topic_or_404(db: Session, topic_id: int):
    item = db.scalar(select(LearningTopic).where(LearningTopic.id == topic_id, LearningTopic.is_active.is_(True)))
    if item is None:
        not_found("Learning topic not found")
    return item


def category_read(item):
    return {key: getattr(item, key) for key in ("id", "name", "slug", "description", "icon", "display_order")}


def progress_read(item):
    if item is None:
        return {"completed": False, "progress_percent": 0, "questions_attempted": 0, "questions_correct": 0, "practice_accuracy": None, "last_practiced_at": None}
    accuracy = round(item.questions_correct / item.questions_attempted * 100, 1) if item.questions_attempted else None
    return {"completed": item.completed, "progress_percent": item.progress_percent,
        "questions_attempted": item.questions_attempted, "questions_correct": item.questions_correct,
        "practice_accuracy": accuracy, "last_practiced_at": item.last_practiced_at}


def topic_read(db: Session, item: LearningTopic, user_id: int | None = None):
    category = db.get(LearningCategory, item.category_id)
    progress = db.scalar(select(LearningProgress).where(LearningProgress.user_id == user_id, LearningProgress.topic_id == item.id)) if user_id else None
    return {"id": item.id, "category_id": item.category_id, "category_name": category.name if category else "",
        "category_slug": category.slug if category else "", "name": item.name, "slug": item.slug,
        "description": item.description, "difficulty": item.difficulty, "estimated_minutes": item.estimated_minutes,
        "display_order": item.display_order, "progress": progress_read(progress)}


def resource_read(item):
    url = item.url
    if url:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            url = None
    return {key: getattr(item, key) for key in ("id", "topic_id", "title", "description", "category",
        "resource_type", "provider", "source", "duration_minutes", "is_verified", "created_at", "updated_at")} | {"url": url}


def categories(db: Session, user_id: int):
    rows = db.scalars(select(LearningCategory).where(LearningCategory.is_active.is_(True)).order_by(LearningCategory.display_order)).all()
    results = []
    for row in rows:
        count = db.scalar(select(func.count(LearningTopic.id)).where(LearningTopic.category_id == row.id, LearningTopic.is_active.is_(True)))
        progress_items = db.scalars(select(LearningProgress).join(LearningTopic, LearningTopic.id == LearningProgress.topic_id)
            .where(LearningProgress.user_id == user_id, LearningTopic.category_id == row.id)).all()
        results.append({**category_read(row), "topic_count": count or 0,
            "progress_percent": round(sum(p.progress_percent for p in progress_items) / count) if count and progress_items else 0})
    return results


def category_detail(db: Session, user_id: int, category_id: int):
    item = category_or_404(db, category_id)
    topics = db.scalars(select(LearningTopic).where(LearningTopic.category_id == item.id, LearningTopic.is_active.is_(True)).order_by(LearningTopic.display_order)).all()
    return {**category_read(item), "topics": [topic_read(db, topic, user_id) for topic in topics]}


def list_topics(db: Session, user_id: int, category_id: int | None = None, search: str | None = None, offset: int = 0, limit: int = 50):
    stmt = select(LearningTopic).where(LearningTopic.is_active.is_(True))
    if category_id is not None:
        category_or_404(db, category_id)
        stmt = stmt.where(LearningTopic.category_id == category_id)
    if search and search.strip():
        stmt = stmt.where(LearningTopic.name.ilike(f"%{search.strip()}%"))
    rows = db.scalars(stmt.order_by(LearningTopic.category_id, LearningTopic.display_order).offset(offset).limit(limit)).all()
    return {"topics": [topic_read(db, row, user_id) for row in rows], "offset": offset, "limit": limit}


def resources_for_topic(db: Session, user_id: int, topic_id: int):
    topic_or_404(db, topic_id)
    rows = db.scalars(select(LearningResource).where(LearningResource.topic_id == topic_id,
        LearningResource.is_active.is_(True), (LearningResource.user_id.is_(None) | (LearningResource.user_id == user_id)))
        .order_by(LearningResource.id)).all()
    return [resource_read(item) for item in rows]


def topic_detail(db: Session, user_id: int, topic_id: int):
    topic = topic_or_404(db, topic_id)
    difficulty_rows = db.execute(select(PracticeQuestion.difficulty, func.count(PracticeQuestion.id)).where(
        PracticeQuestion.topic_id == topic_id, PracticeQuestion.is_active.is_(True),
        PracticeQuestion.question_type == "mcq", PracticeQuestion.correct_answer.is_not(None)
    ).group_by(PracticeQuestion.difficulty)).all()
    return {**topic_read(db, topic, user_id), "content": topic.content,
        "practice_options": [{"difficulty": level, "question_count": count} for level, count in difficulty_rows],
        "resources": resources_for_topic(db, user_id, topic_id)}


def complete_topic(db: Session, user_id: int, topic_id: int):
    topic = topic_or_404(db, topic_id)
    progress = db.scalar(select(LearningProgress).where(LearningProgress.user_id == user_id, LearningProgress.topic_id == topic_id))
    if progress is None:
        progress = LearningProgress(user_id=user_id, topic_id=topic_id)
        db.add(progress)
    progress.completed = True
    progress.progress_percent = 100
    db.commit()
    db.refresh(progress)
    return {"topic_id": topic.id, "topic": topic.name, **progress_read(progress)}


def progress_list(db: Session, user_id: int, topic_id: int | None = None):
    stmt = select(LearningProgress, LearningTopic).join(LearningTopic, LearningTopic.id == LearningProgress.topic_id).where(LearningProgress.user_id == user_id)
    if topic_id is not None:
        stmt = stmt.where(LearningProgress.topic_id == topic_id)
    rows = db.execute(stmt.order_by(LearningProgress.updated_at.desc())).all()
    return [{"topic_id": topic.id, "topic": topic.name, "category_id": topic.category_id, **progress_read(progress)} for progress, topic in rows]


def recommendations(db: Session, user_id: int, target_role: str | None):
    return build_recommendations(db, user_id, target_role)


def list_resources(db: Session, user_id: int, category: str | None, topic_id: int | None,
                   resource_type: str | None, search: str | None, offset: int, limit: int):
    stmt = select(LearningResource).where(LearningResource.is_active.is_(True),
        (LearningResource.user_id.is_(None) | (LearningResource.user_id == user_id)))
    if category:
        stmt = stmt.where(func.lower(LearningResource.category) == category.casefold())
    if topic_id is not None:
        stmt = stmt.where(LearningResource.topic_id == topic_id)
    if resource_type:
        stmt = stmt.where(LearningResource.resource_type == resource_type)
    if search and search.strip():
        needle = f"%{search.strip()}%"
        stmt = stmt.where(LearningResource.title.ilike(needle) | LearningResource.description.ilike(needle))
    rows = db.scalars(stmt.order_by(LearningResource.created_at.desc()).offset(offset).limit(limit)).all()
    return {"resources": [resource_read(row) for row in rows], "offset": offset, "limit": limit}


def get_resource(db: Session, user_id: int, resource_id: int):
    item = db.scalar(select(LearningResource).where(LearningResource.id == resource_id,
        LearningResource.is_active.is_(True), (LearningResource.user_id.is_(None) | (LearningResource.user_id == user_id))))
    if item is None:
        not_found("Learning resource not found")
    return resource_read(item)


def question_read(question: PracticeQuestion, answer: PracticeAttemptAnswer | None = None, reveal: bool = False):
    result = {"id": question.id, "question": question.question, "question_type": question.question_type,
        "options": question.options, "difficulty": question.difficulty, "source": question.source}
    if answer is not None:
        result.update({"selected_answer": int(answer.selected_answer), "correct": answer.correct,
            "answered": True})
    if reveal:
        result["explanation"] = question.explanation
        if isinstance(question.correct_answer, int) and question.options:
            result["correct_option"] = question.options[question.correct_answer]
        if answer is None:
            result["answered"] = False
    return result


def attempt_or_404(db: Session, user_id: int, attempt_id: int):
    attempt = db.scalar(select(PracticeAttempt).where(PracticeAttempt.id == attempt_id, PracticeAttempt.user_id == user_id))
    if attempt is None:
        not_found("Practice attempt not found")
    return attempt


def attempt_stats(db: Session, attempt: PracticeAttempt):
    answers = db.scalars(select(PracticeAttemptAnswer).where(PracticeAttemptAnswer.attempt_id == attempt.id).order_by(PracticeAttemptAnswer.id)).all()
    answered = len(answers)
    correct = sum(item.correct for item in answers)
    denominator = attempt.total_questions if attempt.status == "completed" else answered
    accuracy = round(correct / denominator * 100, 1) if denominator else 0
    attempt.correct_answers = correct
    attempt.incorrect_answers = answered - correct
    attempt.accuracy = accuracy
    attempt.score = accuracy
    return answers


def current_question(db: Session, attempt: PracticeAttempt):
    answered = set(db.scalars(select(PracticeAttemptAnswer.question_id).where(PracticeAttemptAnswer.attempt_id == attempt.id)).all())
    for question_id in attempt.question_ids:
        if question_id not in answered:
            return db.get(PracticeQuestion, question_id)
    return None


def attempt_read(db: Session, attempt: PracticeAttempt):
    answers = attempt_stats(db, attempt)
    answer_by_question = {answer.question_id: answer for answer in answers}
    review = []
    if attempt.status == "completed":
        for question_id in attempt.question_ids:
            question = db.get(PracticeQuestion, question_id)
            if question:
                review.append(question_read(question, answer_by_question.get(question_id), reveal=True))
    current = current_question(db, attempt) if attempt.status == "in_progress" else None
    topic = db.get(LearningTopic, attempt.topic_id)
    category = db.get(LearningCategory, attempt.category_id)
    return {"id": attempt.id, "topic_id": attempt.topic_id, "topic": topic.name if topic else "",
        "category_id": attempt.category_id, "category": category.name if category else "",
        "total_questions": attempt.total_questions, "answered_count": len(answers),
        "unanswered_count": max(0, attempt.total_questions - len(answers)),
        "correct_answers": attempt.correct_answers, "incorrect_answers": attempt.incorrect_answers,
        "score": attempt.score, "accuracy": attempt.accuracy, "status": attempt.status,
        "started_at": attempt.started_at, "completed_at": attempt.completed_at,
        "current_question": question_read(current) if current else None, "review": review}


def start_practice(db: Session, user_id: int, topic_id: int | None, category_id: int | None,
                   difficulty: str | None, question_count: int):
    if topic_id is not None:
        topic = topic_or_404(db, topic_id)
        if category_id is not None and category_id != topic.category_id:
            raise HTTPException(status_code=422, detail="The selected topic does not belong to this category")
        category_id = topic.category_id
        topics = [topic]
    else:
        stmt = select(LearningTopic).where(LearningTopic.is_active.is_(True))
        if category_id is not None:
            category_or_404(db, category_id)
            stmt = stmt.where(LearningTopic.category_id == category_id)
        topics = db.scalars(stmt.order_by(LearningTopic.display_order)).all()
    if not topics:
        not_found("No learning topics are available yet")
    candidate_rows = []
    for topic in topics:
        stmt = select(PracticeQuestion).where(PracticeQuestion.topic_id == topic.id,
            PracticeQuestion.is_active.is_(True), PracticeQuestion.question_type == "mcq",
            PracticeQuestion.correct_answer.is_not(None))
        if difficulty:
            stmt = stmt.where(PracticeQuestion.difficulty == difficulty)
        questions = db.scalars(stmt).all()
        if questions:
            candidate_rows.extend((topic, question) for question in questions)
    if not candidate_rows:
        raise HTTPException(status_code=404, detail="No scored practice questions are available for these filters yet.")
    eligible_topics = {}
    for topic, question in candidate_rows:
        eligible_topics.setdefault(topic.id, (topic, []) )[1].append(question)
    topic, eligible_questions = random.choice(list(eligible_topics.values()))
    random.shuffle(eligible_questions)
    selected = eligible_questions[:min(question_count, 20)]
    attempt = PracticeAttempt(user_id=user_id, topic_id=topic.id, category_id=topic.category_id,
        question_ids=[question.id for question in selected], total_questions=len(selected), status="in_progress")
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt_read(db, attempt)


def update_progress(db: Session, attempt: PracticeAttempt, correct: bool):
    progress = db.scalar(select(LearningProgress).where(LearningProgress.user_id == attempt.user_id, LearningProgress.topic_id == attempt.topic_id))
    if progress is None:
        progress = LearningProgress(user_id=attempt.user_id, topic_id=attempt.topic_id,
            completed=False, progress_percent=0, questions_attempted=0, questions_correct=0)
        db.add(progress)
    progress.questions_attempted += 1
    progress.questions_correct += 1 if correct else 0
    progress.progress_percent = 100 if progress.completed else min(90, progress.questions_attempted * 10)
    progress.last_practiced_at = utc_now()


def answer_practice(db: Session, user_id: int, attempt_id: int, question_id: int, selected_answer: int):
    attempt = attempt_or_404(db, user_id, attempt_id)
    if attempt.status != "in_progress":
        raise HTTPException(status_code=409, detail="This practice attempt is complete and cannot be changed.")
    question = db.scalar(select(PracticeQuestion).where(PracticeQuestion.id == question_id,
        PracticeQuestion.topic_id == attempt.topic_id, PracticeQuestion.is_active.is_(True)))
    if question is None or question.id not in attempt.question_ids:
        raise HTTPException(status_code=404, detail="Question does not belong to this practice attempt.")
    if db.scalar(select(PracticeAttemptAnswer.id).where(PracticeAttemptAnswer.attempt_id == attempt.id,
            PracticeAttemptAnswer.question_id == question.id)):
        raise HTTPException(status_code=409, detail="An answer has already been submitted for this question.")
    pending = current_question(db, attempt)
    if pending is None or pending.id != question.id:
        raise HTTPException(status_code=409, detail="Answer the current question before continuing.")
    if not question.options or selected_answer < 0 or selected_answer >= len(question.options):
        raise HTTPException(status_code=422, detail="Select one of the available options.")
    correct = selected_answer == question.correct_answer
    answer = PracticeAttemptAnswer(attempt_id=attempt.id, question_id=question.id,
        selected_answer=str(selected_answer), correct=correct)
    db.add(answer)
    try:
        db.flush()
        answers = attempt_stats(db, attempt)
        update_progress(db, attempt, correct)
        if len(answers) >= attempt.total_questions:
            attempt.status = "completed"
            attempt.completed_at = utc_now()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An answer has already been submitted for this question.") from None
    db.refresh(attempt)
    result = {"correct": correct, "explanation": question.explanation,
        "answered_count": len(answers), "total_questions": attempt.total_questions,
        "correct_answers": attempt.correct_answers, "incorrect_answers": attempt.incorrect_answers,
        "accuracy": attempt.accuracy, "completed": attempt.status == "completed"}
    if isinstance(question.correct_answer, int) and question.options:
        result["correct_option"] = question.options[question.correct_answer]
    if attempt.status == "in_progress":
        next_q = current_question(db, attempt)
        result["next_question"] = question_read(next_q) if next_q else None
    else:
        result["attempt"] = attempt_read(db, attempt)
    return result


def complete_practice(db: Session, user_id: int, attempt_id: int):
    attempt = attempt_or_404(db, user_id, attempt_id)
    if attempt.status == "in_progress":
        attempt.status = "completed"
        attempt.completed_at = utc_now()
        attempt_stats(db, attempt)
        db.commit()
    return attempt_read(db, attempt)


def practice_history(db: Session, user_id: int, category_id: int | None, topic_id: int | None,
                     date_from: date | None, date_to: date | None, offset: int, limit: int):
    stmt = select(PracticeAttempt).where(PracticeAttempt.user_id == user_id)
    if category_id is not None:
        stmt = stmt.where(PracticeAttempt.category_id == category_id)
    if topic_id is not None:
        stmt = stmt.where(PracticeAttempt.topic_id == topic_id)
    if date_from:
        stmt = stmt.where(PracticeAttempt.started_at >= datetime.combine(date_from, time.min, timezone.utc))
    if date_to:
        stmt = stmt.where(PracticeAttempt.started_at <= datetime.combine(date_to, time.max, timezone.utc))
    rows = db.scalars(stmt.order_by(PracticeAttempt.started_at.desc()).offset(offset).limit(limit)).all()
    results = []
    for item in rows:
        attempt_stats(db, item)
        topic = db.get(LearningTopic, item.topic_id)
        category = db.get(LearningCategory, item.category_id)
        results.append({"id": item.id, "topic_id": item.topic_id, "topic": topic.name if topic else "",
            "category_id": item.category_id, "category": category.name if category else "",
            "total_questions": item.total_questions, "answered_count": item.correct_answers + item.incorrect_answers,
            "unanswered_count": max(0, item.total_questions - item.correct_answers - item.incorrect_answers),
            "correct_answers": item.correct_answers, "incorrect_answers": item.incorrect_answers,
            "score": item.score, "accuracy": item.accuracy, "status": item.status,
            "started_at": item.started_at, "completed_at": item.completed_at})
    return {"attempts": results, "offset": offset, "limit": limit}
