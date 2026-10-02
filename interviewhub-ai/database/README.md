# Database setup

Create a MySQL database and a least-privilege application user, then set `DATABASE_URL` in the project `.env` file. Example database creation (run as a MySQL administrator):

```sql
CREATE DATABASE interviewhub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'interviewhub_app'@'localhost' IDENTIFIED BY 'set-a-local-password';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES ON interviewhub.* TO 'interviewhub_app'@'localhost';
```

Use that account in `DATABASE_URL`; do not commit the password. In development, starting the backend runs SQLAlchemy `Base.metadata.create_all`, which creates missing tables and does not drop existing tables. Additive development migrations add nullable `interview_sessions.resume_id` and `interview_sessions.company_id` columns to existing SQLite/MySQL databases.

Production does not run schema or data seeding automatically. Apply reviewed migrations for Phases 5 and 6 before deployment as documented in the project README. For Phase 7, back up the target and run `python -m app.db.migrate_phase7` from `backend` to create missing learning tables; then run `python -m app.db.seed_learning` to insert InterviewHub-authored starter content. For Phase 8, back up and review the target, then run `python -m app.db.migrate_phase8` from `backend`; this adds defaulted interview context/question fields and creates the evaluation/report tables. No existing interview answers are dropped. MySQL execution has not been verified here. Introduce Alembic before further evolving deployed schemas.
