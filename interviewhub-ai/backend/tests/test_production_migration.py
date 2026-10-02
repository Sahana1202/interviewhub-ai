from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.db.base import Base
from app.db.migrate_production import migrate_production
from app.models.learning import LearningCategory, LearningTopic, PracticeQuestion
from app.models.user import User


def test_production_migration_creates_complete_sqlite_schema_idempotently():
    database_path = Path(__file__).resolve().parent / f".phase11-migration-{uuid4().hex}.sqlite3"
    engine = create_engine(f"sqlite:///{database_path}")
    try:
        migrate_production(engine)
        with Session(engine) as db:
            user = User(name="Preserved User", email="preserved@example.com", password_hash="test-hash")
            db.add(user)
            db.commit()
            before = tuple(db.scalar(select(func.count()).select_from(model)) for model in
                           (LearningCategory, LearningTopic, PracticeQuestion))
            assert all(count > 0 for count in before)

        migrate_production(engine)
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(User).where(User.email == "preserved@example.com")) == 1
            after = tuple(db.scalar(select(func.count()).select_from(model)) for model in
                          (LearningCategory, LearningTopic, PracticeQuestion))
            assert after == before
            assert "interview_reports" in Base.metadata.tables
            assert "admin_activity_logs" in Base.metadata.tables
    finally:
        engine.dispose()
        database_path.unlink(missing_ok=True)
