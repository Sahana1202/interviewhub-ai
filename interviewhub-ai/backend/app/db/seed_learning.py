from app.db.database import SessionLocal
from app.services.learning_seed_service import seed_learning_catalog


def main():
    with SessionLocal() as db:
        seed_learning_catalog(db)


if __name__ == "__main__":
    main()
