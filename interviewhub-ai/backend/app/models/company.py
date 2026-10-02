from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(200), unique=True, index=True, nullable=False)
    industry: Mapped[str | None] = mapped_column(String(160))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    headquarters: Mapped[str | None] = mapped_column(String(200))
    website: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    sources: Mapped[list["CompanySource"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    technologies: Mapped[list["CompanyTechnology"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    roles: Mapped[list["CompanyRole"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    reports: Mapped[list["CompanyInterviewReport"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    topics: Mapped[list["CompanyInterviewTopic"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class CompanySource(Base):
    __tablename__ = "company_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(200))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    company: Mapped[Company] = relationship(back_populates="sources")


class CompanyTechnology(Base):
    __tablename__ = "company_technologies"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    technology: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="Other")
    source_id: Mapped[int] = mapped_column(ForeignKey("company_sources.id", ondelete="CASCADE"), nullable=False)
    confidence: Mapped[str] = mapped_column(String(30), default="documented", nullable=False)
    company: Mapped[Company] = relationship(back_populates="technologies")


class CompanyRole(Base):
    __tablename__ = "company_roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    employment_type: Mapped[str | None] = mapped_column(String(80))
    skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("company_sources.id", ondelete="CASCADE"), nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)
    company: Mapped[Company] = relationship(back_populates="roles")


class CompanyInterviewReport(Base):
    __tablename__ = "company_interview_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str | None] = mapped_column(String(200))
    experience_level: Mapped[str | None] = mapped_column(String(80))
    process_summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("company_sources.id", ondelete="CASCADE"), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False)
    company: Mapped[Company] = relationship(back_populates="reports")


class CompanyInterviewTopic(Base):
    __tablename__ = "company_interview_topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("company_sources.id", ondelete="CASCADE"), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False)
    company: Mapped[Company] = relationship(back_populates="topics")


class CompanyQuizQuestion(Base):
    __tablename__ = "company_quiz_questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)
    correct_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("company_sources.id", ondelete="CASCADE"), nullable=False)


class CompanyQuizAttempt(Base):
    __tablename__ = "company_quiz_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("company_quiz_questions.id", ondelete="CASCADE"), nullable=False)
    selected_answer: Mapped[int] = mapped_column(Integer, nullable=False)
    correct: Mapped[bool] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserCompanyBookmark(Base):
    __tablename__ = "user_company_bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="uq_user_company_bookmark"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
