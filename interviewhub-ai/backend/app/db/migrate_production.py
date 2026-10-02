"""Explicit additive production schema setup and upgrade.

Review and back up the target before running:
    ENVIRONMENT=production python -m app.db.migrate_production

This command creates missing tables, applies the existing additive compatibility
migrations, and idempotently seeds InterviewHub-owned learning content. It does
not drop tables, alter existing values beyond documented defaulted migrations,
or run automatically during application startup.
"""
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app import models  # noqa: F401 - register the complete model metadata
from app.core.config import settings
from app.db.base import Base
from app.db.database import engine
from app.db.migrations import (
    ensure_interview_company_column,
    ensure_interview_resume_column,
    ensure_onboarding_completed_column,
    ensure_phase8_interview_columns,
    ensure_phase9_admin_schema,
)
from app.services.learning_seed_service import seed_learning_catalog


def migrate_production(target: Engine) -> None:
    """Create missing schema and run only the project's reviewed additive migrations."""
    Base.metadata.create_all(bind=target, checkfirst=True)
    ensure_onboarding_completed_column(target)
    ensure_interview_resume_column(target)
    ensure_interview_company_column(target)
    ensure_phase8_interview_columns(target)
    ensure_phase9_admin_schema(target)
    with Session(target) as db:
        seed_learning_catalog(db)


def main() -> None:
    if settings.environment.lower() != "production":
        raise SystemExit("Set ENVIRONMENT=production before running production migrations.")
    if engine.dialect.name != "mysql":
        raise SystemExit("Production migrations require the configured MySQL database.")
    migrate_production(engine)
    print("Production schema is ready. No tables were dropped.")


if __name__ == "__main__":
    main()
