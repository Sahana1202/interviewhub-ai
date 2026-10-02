from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InterviewStatus(str, Enum):
    SETUP = "setup"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewType(str, Enum):
    HR = "HR"
    TECHNICAL = "Technical"
    COMBINED = "Combined"


class InterviewDifficulty(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class ResponseMode(str, Enum):
    TEXT = "text"
    VOICE = "voice"


class QuestionCategory(str, Enum):
    HR = "HR"
    TECHNICAL = "Technical"
    BEHAVIORAL = "Behavioral"
    SITUATIONAL = "Situational"
    INTRODUCTION = "Introduction"
    ROLE_SPECIFIC = "Role Specific"
    PROJECT = "Project"
    RESUME = "Resume"
    COMPANY = "Company"
    APTITUDE = "Aptitude"
    COMMUNICATION = "Communication"
def values(enum_class):
    return [item.value for item in enum_class]


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), index=True)
    company_name: Mapped[str | None] = mapped_column(String(160))
    job_role: Mapped[str] = mapped_column(String(120), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(40), nullable=False)
    interview_type: Mapped[InterviewType] = mapped_column(SAEnum(InterviewType, native_enum=False, values_callable=values), nullable=False)
    difficulty: Mapped[InterviewDifficulty] = mapped_column(SAEnum(InterviewDifficulty, native_enum=False, values_callable=values), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    interviewer_id: Mapped[str] = mapped_column(String(40), nullable=False)
    advanced_interview_type: Mapped[str] = mapped_column(String(40), nullable=False, default="Mixed Interview", server_default="Mixed Interview")
    difficulty_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed", server_default="fixed")
    current_difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="Intermediate", server_default="Intermediate")
    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    response_mode: Mapped[ResponseMode] = mapped_column(SAEnum(ResponseMode, native_enum=False, values_callable=values), nullable=False)
    status: Mapped[InterviewStatus] = mapped_column(SAEnum(InterviewStatus, native_enum=False, values_callable=values), default=InterviewStatus.SETUP, nullable=False)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remaining_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    questions: Mapped[list["InterviewQuestion"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.sequence_number")
    resume: Mapped["Resume | None"] = relationship(back_populates="interview_sessions")
    company: Mapped["Company | None"] = relationship()


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    __table_args__ = (UniqueConstraint("session_id", "sequence_number", name="uq_interview_question_sequence"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[QuestionCategory] = mapped_column(SAEnum(QuestionCategory, native_enum=False, values_callable=values), nullable=False)
    difficulty: Mapped[InterviewDifficulty] = mapped_column(SAEnum(InterviewDifficulty, native_enum=False, values_callable=values), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    question_source: Mapped[str] = mapped_column(String(24), nullable=False, default="practice_question", server_default="practice_question")
    parent_question_id: Mapped[int | None] = mapped_column(ForeignKey("interview_questions.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session: Mapped[InterviewSession] = relationship(back_populates="questions")
    answer: Mapped["InterviewAnswer | None"] = relationship(back_populates="question", cascade="all, delete-orphan", uselist=False)


class InterviewEvaluation(Base):
    __tablename__ = "interview_evaluations"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True, nullable=False)
    answer_id: Mapped[int] = mapped_column(ForeignKey("interview_answers.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    overall_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    strengths_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    improvements_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    technical_accuracy: Mapped[float | None] = mapped_column(Float)
    relevance: Mapped[float | None] = mapped_column(Float)
    clarity: Mapped[float | None] = mapped_column(Float)
    completeness: Mapped[float | None] = mapped_column(Float)
    follow_up_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    answer: Mapped["InterviewAnswer"] = relationship(back_populates="evaluation")


class InterviewReport(Base):
    __tablename__ = "interview_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    improvement_areas_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    topic_breakdown_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    communication_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    technical_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_topics_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    question_feedback_json: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("interview_questions.id", ondelete="CASCADE"), unique=True, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text)
    response_mode: Mapped[ResponseMode] = mapped_column(SAEnum(ResponseMode, native_enum=False, values_callable=values), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    question: Mapped[InterviewQuestion] = relationship(back_populates="answer")
    evaluation: Mapped["InterviewEvaluation | None"] = relationship(back_populates="answer", uselist=False, cascade="all, delete-orphan")
