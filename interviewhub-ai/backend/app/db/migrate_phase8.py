"""Explicit additive Phase 8 migration for production databases."""
from app.db.database import engine
from app.db.migrations import migrate_phase8


if __name__ == "__main__":
    migrate_phase8(engine)
    print("Phase 8 schema migration completed (additive changes only).")
