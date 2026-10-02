"""Apply the additive Phase 9 user role and administrator audit schema."""
from app.db.database import engine
from app.db.migrations import ensure_phase9_admin_schema


if __name__ == "__main__":
    ensure_phase9_admin_schema(engine)
    print("Phase 9 additive migration completed.")
