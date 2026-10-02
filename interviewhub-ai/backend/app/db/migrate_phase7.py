"""Explicit, idempotent Phase 7 table creation for an already-migrated deployment.

Run only after reviewing the database backup and target DATABASE_URL:
    python -m app.db.migrate_phase7
This creates missing Phase 7 tables; it does not alter existing tables or seed content.
"""
from app.db.base import Base
from app.db.database import engine
from app import models  # noqa: F401 - register all model metadata


PHASE_7_TABLES = (
    "learning_categories",
    "learning_topics",
    "learning_resources",
    "practice_questions",
    "practice_attempts",
    "practice_attempt_answers",
    "learning_progress",
)


def main():
    Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[name] for name in PHASE_7_TABLES], checkfirst=True)


if __name__ == "__main__":
    main()
