from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    file_name: str
    file_size: int
    mime_type: str
    status: str
    processing_message: str | None
    created_at: datetime


class ResumeDetail(ResumeSummary):
    contact: dict
    education: list[dict]
    skills: list[str]
    projects: list[dict]
    experience: list[dict]
    certifications: list[str]
    achievements: list[str]
    completeness: dict
    suggestions: list[str]
    practice_questions: list[str]


class InterviewContext(BaseModel):
    resume_id: int
    file_name: str
    skills: list[str]
    projects: list[dict]
    experience: list[dict]
    education: list[dict]
    certifications: list[str]
