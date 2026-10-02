"""Promote an existing account to administrator from a trusted server shell."""
import argparse
import getpass

from sqlalchemy import select

from app.core.security import verify_password
from app.db.database import SessionLocal, engine
from app.db.migrations import ensure_phase9_admin_schema
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely provision an InterviewHub administrator")
    parser.add_argument("email", help="Email of an already registered account")
    args = parser.parse_args()
    ensure_phase9_admin_schema(engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email.strip().lower()))
        if user is None:
            parser.error("No existing account uses that email. Register it first, then rerun this command.")
        if not user.is_active:
            parser.error("The account is inactive; reactivate it before administrator provisioning.")
        password = getpass.getpass("Confirm the account password: ")
        if not verify_password(password, user.password_hash):
            parser.error("Password confirmation failed.")
        if user.role == "admin":
            print("This account is already an administrator.")
            return
        user.role = "admin"
        db.commit()
        print(f"Administrator role granted to {user.email} (user ID {user.id}).")


if __name__ == "__main__":
    main()
