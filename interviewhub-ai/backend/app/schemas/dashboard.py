from pydantic import BaseModel, ConfigDict


class DashboardProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_role: str | None
    target_industry: str | None
    experience_level: str | None


class DashboardProgress(BaseModel):
    technical: int | None = None
    aptitude: int | None = None
    english: int | None = None
    interview: int | None = None


class DashboardActivity(BaseModel):
    id: str
    title: str
    description: str
    occurred_at: str


class DashboardLearningProgress(BaseModel):
    topic_id: int
    topic: str
    category_id: int
    progress_percent: int
    completed: bool
    practice_accuracy: float | None


class DashboardLearningRecommendation(BaseModel):
    topic_id: int
    topic: str
    category_id: int
    reason: str


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    profile: DashboardProfile
    profile_completion: int
    progress: DashboardProgress
    recommended_topics: list[str]
    recent_activity: list[DashboardActivity]
    learning_progress: list[DashboardLearningProgress] = []
    recommended_learning: list[DashboardLearningRecommendation] = []
