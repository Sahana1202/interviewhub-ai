from sqlalchemy import Engine, inspect


def ensure_phase9_admin_schema(engine: Engine) -> None:
    """Add candidate/admin roles and append-only audit storage without dropping data."""
    from app import models  # noqa: F401
    from app.db.base import Base

    inspector = inspect(engine)
    if inspector.has_table("users") and "role" not in {c["name"] for c in inspector.get_columns("users")}:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'candidate'")
    Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables["admin_activity_logs"]], checkfirst=True)


def ensure_onboarding_completed_column(engine: Engine) -> None:
    """Add the Phase 2 profile flag to existing development databases without dropping data."""
    inspector = inspect(engine)
    if not inspector.has_table("user_profiles"):
        return
    columns = {column["name"] for column in inspector.get_columns("user_profiles")}
    if "onboarding_completed" in columns:
        return
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "ALTER TABLE user_profiles ADD COLUMN onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE"
        )


def ensure_interview_resume_column(engine: Engine) -> None:
    """Add the optional Phase 5 relationship without changing existing interviews."""
    inspector = inspect(engine)
    if not inspector.has_table("interview_sessions"):
        return
    if "resume_id" in {column["name"] for column in inspector.get_columns("interview_sessions")}:
        return
    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE interview_sessions ADD COLUMN resume_id INTEGER NULL")
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql(
                "CREATE INDEX IF NOT EXISTS ix_interview_sessions_resume_id ON interview_sessions (resume_id)"
            )
        else:
            connection.exec_driver_sql(
                "ALTER TABLE interview_sessions ADD CONSTRAINT fk_interview_sessions_resume_id_resumes "
                "FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL"
            )
            connection.exec_driver_sql("CREATE INDEX ix_interview_sessions_resume_id ON interview_sessions (resume_id)")


def ensure_interview_company_column(engine: Engine) -> None:
    """Add the optional Phase 6 company relationship without changing existing sessions."""
    inspector = inspect(engine)
    if not inspector.has_table("interview_sessions"):
        return
    if "company_id" in {column["name"] for column in inspector.get_columns("interview_sessions") }:
        return
    with engine.begin() as connection:
        connection.exec_driver_sql("ALTER TABLE interview_sessions ADD COLUMN company_id INTEGER NULL")
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_interview_sessions_company_id ON interview_sessions (company_id)")
            # SQLite cannot add a foreign key constraint to an existing table in-place.
            # Keep old session references safe when a managed company record is removed.
            connection.exec_driver_sql(
                "CREATE TRIGGER IF NOT EXISTS trg_company_delete_clear_interview_context "
                "AFTER DELETE ON companies BEGIN UPDATE interview_sessions SET company_id = NULL "
                "WHERE company_id = OLD.id; END"
            )
        else:
            connection.exec_driver_sql(
                "ALTER TABLE interview_sessions ADD CONSTRAINT fk_interview_sessions_company_id_companies "
                "FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL"
            )
            connection.exec_driver_sql("CREATE INDEX ix_interview_sessions_company_id ON interview_sessions (company_id)")


def ensure_phase8_interview_columns(engine: Engine) -> None:
    """Add Phase 8 fields in place, preserving existing interview rows."""
    inspector = inspect(engine)
    if inspector.has_table("interview_sessions"):
        existing = {column["name"] for column in inspector.get_columns("interview_sessions")}
        definitions = {
            "advanced_interview_type": "VARCHAR(40) NOT NULL DEFAULT 'Mixed Interview'",
            "difficulty_mode": "VARCHAR(20) NOT NULL DEFAULT 'fixed'",
            "current_difficulty": "VARCHAR(20) NOT NULL DEFAULT 'Intermediate'",
            "ai_enabled": "BOOLEAN NOT NULL DEFAULT 0",
        }
        added_current_difficulty = "current_difficulty" not in existing
        for name, definition in definitions.items():
            if name not in existing:
                with engine.begin() as connection:
                    connection.exec_driver_sql(f"ALTER TABLE interview_sessions ADD COLUMN {name} {definition}")
        if added_current_difficulty and "difficulty" in existing:
            with engine.begin() as connection:
                connection.exec_driver_sql("UPDATE interview_sessions SET current_difficulty = difficulty")
    if inspector.has_table("interview_questions"):
        existing = {column["name"] for column in inspector.get_columns("interview_questions")}
        definitions = {
            "question_source": "VARCHAR(24) NOT NULL DEFAULT 'practice_question'",
            "parent_question_id": "INTEGER NULL",
        }
        for name, definition in definitions.items():
            if name not in existing:
                with engine.begin() as connection:
                    connection.exec_driver_sql(f"ALTER TABLE interview_questions ADD COLUMN {name} {definition}")
    inspector = inspect(engine)
    if inspector.has_table("interview_reports") and "question_feedback_json" not in {column["name"] for column in inspector.get_columns("interview_reports")}:
        with engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE interview_reports ADD COLUMN question_feedback_json JSON NULL")


def migrate_phase8(engine: Engine) -> None:
    """Create Phase 8 evaluation/report tables and add defaulted fields only."""
    from app import models  # noqa: F401
    from app.db.base import Base
    ensure_phase8_interview_columns(engine)
    Base.metadata.create_all(bind=engine, tables=[
        Base.metadata.tables["interview_evaluations"], Base.metadata.tables["interview_reports"],
    ], checkfirst=True)
    if inspect(engine).has_table("interview_reports"):
        names = {column["name"] for column in inspect(engine).get_columns("interview_reports")}
        if "question_feedback_json" not in names:
            with engine.begin() as connection:
                connection.exec_driver_sql("ALTER TABLE interview_reports ADD COLUMN question_feedback_json JSON NULL")
