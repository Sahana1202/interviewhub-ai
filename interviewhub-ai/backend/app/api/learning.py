from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.services.placement_resource_service import placement_resource_status
from app.services import learning_service

learning_router = APIRouter(prefix="/learning", tags=["learning"])
practice_router = APIRouter(prefix="/practice", tags=["practice"])
resources_router = APIRouter(prefix="/resources", tags=["learning resources"])


class PracticeStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)
    difficulty: Literal["Easy", "Medium", "Hard"] | None = None
    question_count: int = Field(default=10, ge=1, le=20)


class PracticeAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: int = Field(gt=0)
    selected_answer: int = Field(ge=0, le=10)


@learning_router.get("/categories")
def get_categories(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"categories": learning_service.categories(db, user.id)}


@learning_router.get("/categories/{category_id}")
def get_category(category_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.category_detail(db, user.id, category_id)


@learning_router.get("/topics")
def get_topics(category_id: int | None = Query(default=None, gt=0), search: str | None = None,
               offset: int = Query(default=0, ge=0), limit: int = Query(default=50, ge=1, le=100),
               user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.list_topics(db, user.id, category_id, search, offset, limit)


@learning_router.get("/topics/{topic_id}/resources")
def get_topic_resources(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"resources": learning_service.resources_for_topic(db, user.id, topic_id)}


@learning_router.post("/topics/{topic_id}/complete")
def mark_topic_complete(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.complete_topic(db, user.id, topic_id)


@learning_router.get("/topics/{topic_id}")
def get_topic(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.topic_detail(db, user.id, topic_id)


@learning_router.get("/progress")
def get_progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"progress": learning_service.progress_list(db, user.id)}


@learning_router.get("/progress/{topic_id}")
def get_topic_progress(topic_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    learning_service.topic_or_404(db, topic_id)
    items = learning_service.progress_list(db, user.id, topic_id)
    return items[0] if items else {"topic_id": topic_id, **learning_service.progress_read(None)}


@learning_router.get("/recommendations")
def get_recommendations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = user.profile.target_role if user.profile else None
    return learning_service.recommendations(db, user.id, role)


@practice_router.post("/start", status_code=201)
def start_practice(payload: PracticeStartRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.start_practice(db, user.id, payload.topic_id, payload.category_id, payload.difficulty, payload.question_count)


@practice_router.get("/history")
def get_practice_history(category_id: int | None = Query(default=None, gt=0),
                         topic_id: int | None = Query(default=None, gt=0),
                         date_from: date | None = None, date_to: date | None = None,
                         offset: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100),
                         user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not be after date_to")
    return learning_service.practice_history(db, user.id, category_id, topic_id, date_from, date_to, offset, limit)


@practice_router.get("/{attempt_id}")
def get_attempt(attempt_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.attempt_read(db, learning_service.attempt_or_404(db, user.id, attempt_id))


@practice_router.post("/{attempt_id}/answer")
def submit_answer(attempt_id: int, payload: PracticeAnswerRequest,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.answer_practice(db, user.id, attempt_id, payload.question_id, payload.selected_answer)


@practice_router.post("/{attempt_id}/complete")
def complete_attempt(attempt_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.complete_practice(db, user.id, attempt_id)


@resources_router.get("")
def get_resources(category: str | None = None, topic_id: int | None = Query(default=None, gt=0),
                  resource_type: Literal["article", "video", "pdf", "documentation", "practice", "reference", "internal"] | None = None,
                  search: str | None = None, offset: int = Query(default=0, ge=0),
                  limit: int = Query(default=20, ge=1, le=100),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = learning_service.list_resources(db, user.id, category, topic_id, resource_type, search, offset, limit)
    result["placement_source"] = placement_resource_status()
    return result


@resources_router.get("/{resource_id}")
def get_resource(resource_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return learning_service.get_resource(db, user.id, resource_id)
