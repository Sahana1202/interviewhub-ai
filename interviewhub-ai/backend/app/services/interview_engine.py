"""Deterministic starter question bank. Questions are general practice prompts, not company facts."""

from sqlalchemy.orm import Session

from app.models.interview import InterviewQuestion, InterviewSession, QuestionCategory

QUESTION_BANK = (
    ("Tell me about yourself.", QuestionCategory.INTRODUCTION),
    ("Why are you interested in this role?", QuestionCategory.HR),
    ("What is object-oriented programming?", QuestionCategory.TECHNICAL),
    ("Tell me about a time you worked in a team.", QuestionCategory.BEHAVIORAL),
    ("What is an API, and how have you used one?", QuestionCategory.ROLE_SPECIFIC),
    ("Describe a situation where you had to learn something quickly.", QuestionCategory.SITUATIONAL),
    ("What are your strengths, and how do they help you in this role?", QuestionCategory.HR),
    ("What is the difference between GET and POST?", QuestionCategory.TECHNICAL),
    ("Tell me about a challenge you faced and how you handled it.", QuestionCategory.BEHAVIORAL),
    ("What interests you about the technical problems in this role?", QuestionCategory.ROLE_SPECIFIC),
    ("Tell me about a mistake you made and what you learned from it.", QuestionCategory.SITUATIONAL),
    ("Why should we consider you for this role?", QuestionCategory.HR),
    ("What is a database index, and when is it useful?", QuestionCategory.TECHNICAL),
)

TYPE_CATEGORIES = {
    "HR": (QuestionCategory.INTRODUCTION, QuestionCategory.HR, QuestionCategory.BEHAVIORAL, QuestionCategory.SITUATIONAL),
    "Technical": (QuestionCategory.INTRODUCTION, QuestionCategory.TECHNICAL, QuestionCategory.ROLE_SPECIFIC, QuestionCategory.BEHAVIORAL),
    "Combined": (QuestionCategory.INTRODUCTION, QuestionCategory.HR, QuestionCategory.TECHNICAL, QuestionCategory.BEHAVIORAL, QuestionCategory.SITUATIONAL, QuestionCategory.ROLE_SPECIFIC),
}


def question_limit(session: InterviewSession) -> int:
    allowed = TYPE_CATEGORIES[session.interview_type.value]
    available = sum(category in allowed for _, category in QUESTION_BANK)
    return min(available, max(4, session.duration_minutes // 2))


def create_next_question(db: Session, session: InterviewSession) -> InterviewQuestion | None:
    sequence = session.current_question_index + 1
    if sequence > question_limit(session):
        return None
    existing = {question.question_text for question in session.questions}
    categories = TYPE_CATEGORIES[session.interview_type.value]
    ordered_categories = categories[(sequence - 1) % len(categories):] + categories[:(sequence - 1) % len(categories)]
    candidate = None
    for category in ordered_categories:
        candidate = next((item for item in QUESTION_BANK if item[1] == category and item[0] not in existing), None)
        if candidate:
            break
    if candidate is None:
        candidate = next((item for item in QUESTION_BANK if item[1] in categories and item[0] not in existing), None)
    if candidate is None:
        return None
    question = InterviewQuestion(
        session_id=session.id,
        question_text=candidate[0],
        category=candidate[1],
        difficulty=session.difficulty,
        sequence_number=sequence,
        is_follow_up=False,
    )
    db.add(question)
    session.current_question_index = sequence
    db.flush()
    session.questions.append(question) if question not in session.questions else None
    return question
