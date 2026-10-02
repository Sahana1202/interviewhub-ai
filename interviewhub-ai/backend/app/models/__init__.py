"""SQLAlchemy models registered for metadata creation."""

from app.models.profile import UserProfile
from app.models.resume import Resume
from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession, InterviewEvaluation, InterviewReport
from app.models.skill import Skill, UserSkill
from app.models.user import User
from app.models.company import Company, CompanySource, CompanyTechnology, CompanyRole, CompanyInterviewReport, CompanyInterviewTopic, CompanyQuizQuestion, CompanyQuizAttempt, UserCompanyBookmark
from app.models.learning import LearningCategory, LearningTopic, LearningResource, PracticeQuestion, PracticeAttempt, PracticeAttemptAnswer, LearningProgress
from app.models.admin import AdminActivityLog

__all__ = ["User", "UserProfile", "Skill", "UserSkill", "InterviewSession", "InterviewQuestion", "InterviewAnswer", "InterviewEvaluation", "InterviewReport", "Resume", "Company", "CompanySource", "CompanyTechnology", "CompanyRole", "CompanyInterviewReport", "CompanyInterviewTopic", "CompanyQuizQuestion", "CompanyQuizAttempt", "UserCompanyBookmark", "LearningCategory", "LearningTopic", "LearningResource", "PracticeQuestion", "PracticeAttempt", "PracticeAttemptAnswer", "LearningProgress", "AdminActivityLog"]
