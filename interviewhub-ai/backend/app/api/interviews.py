from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewDetailRead,
    InterviewerProfileRead,
    InterviewListResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    EvaluationRead,
    ReportRead,
    AIStatusRead,
    InterviewQuestionRead,
)
from app.services.interview_service import (
    complete_interview,
    detail_read,
    list_interviews,
    owned_session,
    pause_or_resume,
    session_read,
    start_interview,
    submit_answer,
)
from app.services.interviewers import INTERVIEWERS
from app.services.ai_service import AIService
from app.services.ai_interview_service import (evaluate_answer, generate_final_report, generate_followup,
    generate_question, get_report)

router = APIRouter(prefix="/interviews", tags=["interviews"])
ai_router = APIRouter(prefix="/ai", tags=["AI interview"])


@ai_router.get("/status", response_model=AIStatusRead)
def get_ai_status() -> AIStatusRead:
    return AIStatusRead.model_validate(AIService().status())


@router.get("/interviewers", response_model=list[InterviewerProfileRead])
def get_interviewers(user: User = Depends(get_current_user)) -> list[InterviewerProfileRead]:
    del user
    return [InterviewerProfileRead.model_validate(item) for item in INTERVIEWERS.values() if item["is_active"]]


@router.post("/start", response_model=InterviewStartResponse, status_code=201)
def start(
    payload: InterviewStartRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewStartResponse:
    session, question = start_interview(db, user.id, payload)
    return InterviewStartResponse(session=detail_read(session), current_question=question)


@router.get("", response_model=InterviewListResponse)
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InterviewListResponse:
    return InterviewListResponse(sessions=list_interviews(db, user.id))


@router.get("/{session_id}", response_model=InterviewDetailRead)
def get_interview(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InterviewDetailRead:
    return detail_read(owned_session(db, user.id, session_id))


@router.post("/{session_id}/answer", response_model=InterviewAnswerResponse)
def answer(
    session_id: int,
    payload: InterviewAnswerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewAnswerResponse:
    session, saved, next_question = submit_answer(db, user.id, session_id, payload)
    return InterviewAnswerResponse(
        session=detail_read(session),
        saved_answer=saved,
        next_question=next_question,
        question_set_complete=next_question is None,
        message="Answer saved. Preparing your next question..." if next_question else "Answer saved. You have reached the end of this starter question set.",
    )


@router.post("/{session_id}/pause", response_model=InterviewDetailRead)
def pause(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InterviewDetailRead:
    return detail_read(pause_or_resume(db, user.id, session_id))


@router.post("/{session_id}/complete", response_model=InterviewDetailRead)
def complete(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InterviewDetailRead:
    return detail_read(complete_interview(db, user.id, session_id))


@router.post("/{session_id}/ai/question", response_model=InterviewQuestionRead)
def ai_question(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, user.id, session_id)
    return generate_question(db, user, session, AIService())


@router.post("/{session_id}/answers/{answer_id}/evaluate", response_model=EvaluationRead)
def ai_evaluate(session_id: int, answer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, user.id, session_id)
    return evaluate_answer(db, user, session, answer_id, AIService())


@router.post("/{session_id}/follow-up", response_model=InterviewQuestionRead)
def ai_followup(session_id: int, answer_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, user.id, session_id)
    return generate_followup(db, user, session, answer_id, AIService())


@router.post("/{session_id}/final-evaluation", response_model=ReportRead)
def ai_final_evaluation(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, user.id, session_id)
    return generate_final_report(db, user, session, AIService())


@router.get("/{session_id}/report", response_model=ReportRead)
def ai_report(session_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = owned_session(db, user.id, session_id)
    return get_report(db, session)
