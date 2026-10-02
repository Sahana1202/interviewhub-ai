from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.interview import InterviewDifficulty, InterviewStatus, InterviewType, QuestionCategory, ResponseMode

ExperienceLevel = Literal["Student", "Fresher", "0–1 years", "1–3 years", "3+ years"]
DurationMinutes = Literal[10, 15, 20, 30]
AdvancedInterviewType = Literal["HR Interview", "Technical Interview", "Technical + HR", "Project Interview", "Resume-Based Interview", "Company Preparation Interview", "Mixed Interview"]


class InterviewerProfileRead(BaseModel):
    id: str
    name: str
    gender: str
    role: str
    description: str
    style: list[str]
    avatar_url: str | None
    voice_name: str | None
    is_active: bool


class InterviewStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str | None = Field(default=None, max_length=160)
    job_role: str = Field(min_length=2, max_length=120)
    experience_level: ExperienceLevel
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    duration_minutes: DurationMinutes
    interviewer_id: str = Field(min_length=1, max_length=40)
    response_mode: ResponseMode
    resume_id: int | None = Field(default=None, gt=0)
    company_id: int | None = Field(default=None, gt=0)
    advanced_interview_type: AdvancedInterviewType = "Mixed Interview"
    difficulty_mode: Literal["fixed", "adaptive"] = "fixed"
    current_difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Intermediate"
    ai_enabled: bool = False

    @field_validator("company_name", "job_role")
    @classmethod
    def trim_values(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("job_role")
    @classmethod
    def require_role(cls, value: str | None) -> str:
        if value is None or len(value) < 2:
            raise ValueError("Enter a job role with at least two characters")
        return value


class InterviewAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: int = Field(gt=0)
    answer_text: str | None = Field(default=None, max_length=12000)
    transcript: str | None = Field(default=None, max_length=12000)
    response_mode: ResponseMode
    duration_seconds: int | None = Field(default=None, ge=0, le=3600)

    @field_validator("answer_text", "transcript")
    @classmethod
    def trim_answer(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @model_validator(mode="after")
    def require_answer(self):
        if not (self.answer_text or self.transcript):
            raise ValueError("Enter or dictate an answer before submitting")
        return self


class InterviewAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    answer_text: str
    transcript: str | None
    response_mode: ResponseMode
    duration_seconds: int | None
    submitted_at: datetime


class InterviewQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_text: str
    category: QuestionCategory
    difficulty: InterviewDifficulty
    sequence_number: int
    is_follow_up: bool
    question_source: Literal["practice_question", "ai_generated"] = "practice_question"
    parent_question_id: int | None = None
    created_at: datetime
    answer: InterviewAnswerRead | None = None
    evaluation: dict | None = None


class InterviewSessionRead(BaseModel):
    id: int
    company_id: int | None = None
    company_name: str | None
    job_role: str
    experience_level: str
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    duration_minutes: int
    interviewer_id: str
    advanced_interview_type: AdvancedInterviewType = "Mixed Interview"
    difficulty_mode: Literal["fixed", "adaptive"] = "fixed"
    current_difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Intermediate"
    ai_enabled: bool = False
    interviewer_name: str
    response_mode: ResponseMode
    resume_id: int | None = None
    resume_file_name: str | None = None
    status: InterviewStatus
    current_question_index: int
    remaining_seconds: int
    started_at: datetime | None
    paused_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    question_count: int
    answers_count: int
    evaluations_count: int = 0
    question_limit: int


class InterviewDetailRead(InterviewSessionRead):
    questions: list[InterviewQuestionRead]


class InterviewStartResponse(BaseModel):
    session: InterviewDetailRead
    current_question: InterviewQuestionRead
    question_source: Literal["starter_bank"] = "starter_bank"


class InterviewAnswerResponse(BaseModel):
    session: InterviewDetailRead
    saved_answer: InterviewAnswerRead
    next_question: InterviewQuestionRead | None
    question_set_complete: bool
    message: str


class EvaluationRead(BaseModel):
    id: int
    answer_id: int
    overall_feedback: str
    strengths: list[str]
    areas_to_improve: list[str]
    technical_accuracy: float | None
    relevance: float | None
    clarity: float | None
    completeness: float | None
    follow_up_needed: bool
    source: Literal["ai_generated"] = "ai_generated"
    provider: str
    model: str
    created_at: datetime


class ReportRead(BaseModel):
    id: int
    session_id: int
    summary: str
    strengths: list[str]
    improvement_areas: list[str]
    topic_breakdown: list[dict]
    communication_feedback: str
    technical_feedback: str
    recommended_topics: list[dict]
    question_feedback: list[dict] = Field(default_factory=list)
    provider: str
    model: str
    created_at: datetime


class AIStatusRead(BaseModel):
    available: bool
    provider: str | None
    model: str | None


class InterviewListResponse(BaseModel):
    sessions: list[InterviewSessionRead]
