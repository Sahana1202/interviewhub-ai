from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import InterviewContext, ResumeDetail, ResumeSummary
from app.services.resume_service import delete_resume, owned_resume, parse_resume, read_upload, save_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])


def summary(resume: Resume) -> ResumeSummary:
    return ResumeSummary.model_validate(resume)


def detail(resume: Resume) -> ResumeDetail:
    data = resume.parsed_data or {}
    return ResumeDetail(
        **summary(resume).model_dump(),
        contact=data.get("contact", {}), education=data.get("education", []), skills=data.get("skills", []),
        projects=data.get("projects", []), experience=data.get("experience", []),
        certifications=data.get("certifications", []), achievements=data.get("achievements", []),
        completeness=data.get("completeness", {}),
        suggestions=data.get("suggestions", []), practice_questions=data.get("practice_questions", []),
    )


@router.post("/upload", response_model=ResumeSummary, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data, filename = await read_upload(file)
    resume = save_resume(db, user.id, filename, data)
    return summary(resume)


@router.get("", response_model=list[ResumeSummary])
def list_resumes(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())).all()
    return [summary(item) for item in items]


@router.get("/{resume_id}/interview-context", response_model=InterviewContext)
def resume_context(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = owned_resume(db, user.id, resume_id)
    data = item.parsed_data or {}
    return InterviewContext(resume_id=item.id, file_name=item.file_name, skills=data.get("skills", []),
                           projects=data.get("projects", []), experience=data.get("experience", []),
                           education=data.get("education", []), certifications=data.get("certifications", []))


@router.get("/{resume_id}", response_model=ResumeDetail)
def get_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return detail(owned_resume(db, user.id, resume_id))


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    delete_resume(db, owned_resume(db, user.id, resume_id))
    return None


@router.post("/{resume_id}/analyze", response_model=ResumeDetail)
def analyze_resume(resume_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = owned_resume(db, user.id, resume_id)
    if not item.extracted_text:
        raise HTTPException(status_code=422, detail=item.processing_message or "Resume text is not available for analysis")
    item.parsed_data = parse_resume(item.extracted_text)
    item.status = "processed"
    item.processing_message = None
    db.commit()
    db.refresh(item)
    return detail(item)
