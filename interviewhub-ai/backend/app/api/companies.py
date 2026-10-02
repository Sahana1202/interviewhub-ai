from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session
from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["company intelligence"])


class QuizAnswer(BaseModel):
    question_id: int = Field(gt=0)
    selected_answer: int = Field(ge=0, le=3)


def public_company(company):
    data = company_service.company_read(company)
    data["is_bookmarked"] = False
    return data


@router.get("")
def search(q: str | None = None, offset: int = 0, limit: int = 20,
          user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    del user
    if offset < 0 or not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="Invalid pagination")
    return {"companies": [public_company(c) for c in company_service.search_companies(db, q, offset, limit)],
            "research_status": "Research provider unavailable."}


@router.get("/search")
def search_alias(q: str = "", offset: int = 0, limit: int = 20,
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return search(q, offset, limit, user, db)


@router.get("/bookmarks")
def list_bookmarks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = [public_company(c) for c in company_service.bookmarks(db, user.id)]
    for item in results:
        item["is_bookmarked"] = True
    return {"companies": results}


@router.post("/{company_id}/bookmark", status_code=204)
def save_bookmark(company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_service.toggle_bookmark(db, user.id, company_id, True)


@router.delete("/{company_id}/bookmark", status_code=204)
def remove_bookmark(company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    company_service.toggle_bookmark(db, user.id, company_id, False)


@router.get("/{company_id}/interview-context")
def get_interview_context(company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    del user
    return company_service.interview_context(db, company_id)


@router.get("/{company_id}/quiz")
def get_quiz(company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    del user
    question = company_service.quiz_question(db, company_id)
    return {"id": question.id, "question": question.question, "options": question.options,
            "source_id": question.source_id, "label": "Company Knowledge Practice"}


@router.post("/{company_id}/quiz/answer")
def answer_quiz(company_id: int, payload: QuizAnswer, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return company_service.submit_quiz_answer(db, user.id, company_id, payload.question_id, payload.selected_answer)


@router.get("/{company_id}")
def detail(company_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    del user
    return company_service.company_detail(db, company_id)
