# InterviewHub AI

**Your Personal AI Career & Interview Coach**

InterviewHub AI is a career and interview preparation platform for students, freshers, and job seekers. It includes authentication, Virtual HR practice, resume and company context, Learning & Practice, and an optional advanced interview provider integration. AI interview features remain unavailable until a backend provider is configured.

## Project scope

The project includes a React/Vite frontend, FastAPI backend, MySQL/SQLAlchemy data layer, user/profile/skill/resume/company/learning/interview evaluation models, Argon2 password hashing, JWT authentication, protected routes, a responsive dashboard, profile editing, Virtual HR interview sessions, deterministic resume extraction, source-backed Company Intelligence, Learning & Practice, and an optional OpenAI-compatible AI provider boundary.

No AI or company research provider is configured by default. No company records or simulated company facts are seeded. The supplied SIRI and Alex portrait assets are used by the female and male Virtual HR profiles, named SIRI and Alex.

## Technology stack

- Frontend: React 18, Vite 6, React Router, Axios, Tailwind CSS 3, Lucide React
- Backend: Python, FastAPI, SQLAlchemy 2, Pydantic Settings, PyMySQL
- Security: Argon2 password hashing through `pwdlib`, signed JWT access tokens through PyJWT
- Database: MySQL 8 (or compatible MySQL server)

## Architecture

The frontend calls the API through `frontend/src/services/api.js`; the auth context owns the token and current user state. FastAPI routes validate requests with Pydantic and use reusable SQLAlchemy session and authenticated-user dependencies. Interview, resume, company, learning, and practice work is delegated to feature services. Company research and placement-resource import have explicit provider boundaries. The optional server-side AI interview provider uses structured JSON output and is disabled until configured; no web scraping is configured.

## Folder structure

```text
interviewhub-ai/
├── backend/app/{api,core,db,models,schemas,services}/
├── backend/tests/       # SQLite-backed API and migration tests
├── database/README.md
├── docs/
├── frontend/public/
└── frontend/src/{components,context,hooks,layouts,pages,services,utils}/
```

## Prerequisites

- Python 3.10+
- Node.js 20+ and npm
- MySQL 8+ running locally or reachable from the backend

## MySQL setup

See [database/README.md](database/README.md) for example database and least-privilege application account creation. The backend uses the PyMySQL driver, so the connection URL format is `mysql+pymysql://user:password@host:3306/interviewhub`. URL-encode reserved characters in credentials.

## Environment configuration

Copy `.env.example` to `.env` in the project root and set a strong, unique `JWT_SECRET_KEY` and the actual local MySQL `DATABASE_URL`. Keep `.env` private; it is excluded by `.gitignore`. The Vite frontend uses `VITE_API_BASE_URL` (default `http://localhost:8000/api`) and must not contain secrets.

Example secret generation with Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Backend installation and run

From `interviewhub-ai`:

```powershell
py -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

The backend loads `.env` from the working directory. Start the command from the project root as shown. In development, startup uses SQLAlchemy `create_all` for missing tables, applies additive compatibility columns, and idempotently seeds InterviewHub-owned learning material. It does not drop or reset tables. Production startup deliberately does not run development schema changes or seed content; review the explicit migration and seed commands in the Phase 7 section before deployment.

## Frontend installation and run

In another terminal, from `interviewhub-ai`:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

Optional frontend API URL override: create `frontend/.env.local` with `VITE_API_BASE_URL=http://localhost:8000/api`. Vite variables are public build-time configuration; never put secrets there.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API health response |
| POST | `/api/auth/register` | Create user and empty profile; return user and JWT |
| POST | `/api/auth/login` | Verify credentials; return user and JWT |
| GET | `/api/auth/me` | Return current user and profile (Bearer token required) |
| GET | `/api/profile` | Read the authenticated user’s profile |
| PUT | `/api/profile` | Update the authenticated user’s profile |
| POST | `/api/profile/onboarding` | Save the profile and mark onboarding complete |
| GET | `/api/dashboard` | Return the authenticated user’s dashboard summary |
| GET | `/api/interviews/interviewers` | List active Virtual HR profiles |
| POST | `/api/interviews/start` | Create a session and its first practice question |
| GET | `/api/interviews` | List the authenticated user’s interview sessions |
| GET | `/api/interviews/{id}` | Read one owned session and its questions/answers |
| POST | `/api/interviews/{id}/answer` | Save an answer and create the next practice question |
| POST | `/api/interviews/{id}/pause` | Pause or resume an active session |
| POST | `/api/interviews/{id}/complete` | Complete a session and preserve its answers |
| GET | `/api/ai/status` | Read whether an AI provider is configured; never returns credentials |
| POST | `/api/interviews/{id}/ai/question` | Generate and validate the current question for an AI-enabled session |
| POST | `/api/interviews/{id}/answers/{answer_id}/evaluate` | Save/retrieve one AI practice evaluation for an owned answer |
| POST | `/api/interviews/{id}/follow-up?answer_id=` | Generate a contextual follow-up, limited to two per primary question |
| POST | `/api/interviews/{id}/final-evaluation` | Generate/retrieve an evidence-based practice report for a completed session |
| GET | `/api/interviews/{id}/report` | Read an owned saved AI practice report |
| POST | `/api/resumes/upload` | Authenticated PDF upload and extraction (10 MB max) |
| GET | `/api/resumes` | List the authenticated user’s resumes |
| GET | `/api/resumes/{id}` | Read extracted and structured resume details |
| DELETE | `/api/resumes/{id}` | Delete an owned resume and its stored PDF |
| POST | `/api/resumes/{id}/analyze` | Re-run deterministic structure analysis |
| GET | `/api/resumes/{id}/interview-context` | Return concise owned resume context |
| GET | `/api/companies` and `/api/companies/search?q=` | Search source-backed company records |
| GET | `/api/companies/{id}` | Read company profile, sources, roles, technologies, and interview insights |
| GET | `/api/companies/{id}/interview-context` | Return sourced optional Virtual HR context |
| GET/POST | `/api/companies/{id}/quiz`, `/quiz/answer` | Retrieve a source-backed practice question and submit an answer |
| GET | `/api/companies/bookmarks` | List the signed-in user’s saved companies |
| POST/DELETE | `/api/companies/{id}/bookmark` | Save or remove the signed-in user’s bookmark |
| GET | `/api/learning/categories` | List learning areas and user-specific progress |
| GET | `/api/learning/categories/{id}` | List a category’s topics |
| GET | `/api/learning/topics` | Search and paginate learning topics |
| GET | `/api/learning/topics/{id}` | Read a lesson, resources, practice availability, and progress |
| POST | `/api/learning/topics/{id}/complete` | Explicitly mark a topic complete |
| GET | `/api/learning/progress` | List the signed-in user’s topic progress |
| GET | `/api/learning/recommendations` | Get transparent deterministic next-topic recommendations |
| GET | `/api/resources` and `/api/resources/{id}` | Search resources available to the user |
| POST | `/api/practice/start` | Start an owned MCQ practice attempt |
| GET/POST | `/api/practice/{id}`, `/answer` | Resume an attempt or submit its current answer |
| POST | `/api/practice/{id}/complete` | Finish an attempt and calculate its score |
| GET | `/api/practice/history` | Filter the signed-in user’s saved practice attempts |

Interactive API documentation is available at `/docs` while the backend is running.

## Authentication flow

Registration and login return a signed bearer token and a safe user object. The frontend stores the token in browser `localStorage`, attaches it to API requests, validates it via `/auth/me` on refresh, and redirects according to the server’s `onboarding_completed` flag. Incomplete accounts go to `/onboarding`; completed accounts can use `/dashboard` and `/profile`. Logout and unauthorized API responses clear local auth state. Tokens expire after the configured number of minutes; signing out does not revoke an already issued token server-side. `localStorage` is convenient for this development foundation but is more exposed to successful same-origin script injection than an `HttpOnly` cookie.

## Profile completion and onboarding

Onboarding collects optional education and location details plus a required experience level and target role. The form saves a draft after each step so refreshes retain progress. Completing onboarding updates the authenticated user’s existing one-to-one profile; it does not create another profile row. The profile editor can update the same fields later. Clearing the required target role or experience level through the API marks onboarding incomplete and routes the user back to `/onboarding`.

The dashboard’s profile completion is deterministic: it counts the eight saved education and career fields (`college`, `degree`, `department`, `graduation_year`, `experience_level`, `target_role`, `target_industry`, and `location`). Optional empty fields lower the percentage; there is no AI-derived score.

The supplied placement Drive folder is exposed as an external link in Company Intelligence through `VITE_PLACEMENT_RESOURCES_URL`. The app opens Google Drive in the user’s browser; it does not copy, scrape, or ingest folder contents. Google continues to enforce the folder’s access controls. The supplied SIRI and Alex portraits are mapped to their corresponding Virtual HR profiles.

## Phase 2, 3, and 4 tests

Install development test dependencies and run the backend suite from `backend`:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q -p no:cacheprovider -p no:tmpdir tests
```

The suite uses a disposable SQLite test database. Coverage includes auth/profile, dashboard aggregation, interview setup validation, ownership, question selection, answer and voice transcript persistence, timer expiry, history, AI-unavailable behavior, and lifecycle transitions. The configured MySQL database remains the application target and should be exercised with valid local credentials before deployment.

## Phase 3 dashboard and core UX

The authenticated workspace has responsive navigation for Dashboard, Interview Practice, Resume Analyzer, Job Match, Company Preparation, Learning Hub, Aptitude, English Coach, Learning Roadmap, Performance, and Interview History. The dashboard shows a time-based greeting, the signed-in user’s saved career goals, an eight-field profile completion percentage, four preparation progress states, starter topic suggestions derived from the target role, and recent activity when the backend supports it. At present there are no progress or activity tables, so those sections report “Not started” and an empty state rather than invented metrics.

The following routes intentionally show a reusable “Coming soon” explanation: `/job-match`, `/roadmap`, and `/performance`. Learning, aptitude, English, and placement resources are described below.

The navigation collapses into an accessible drawer on smaller screens. The account menu retains Profile, Settings, and Logout. Dashboard loading and retryable API error states are included.

## Phase 4 — Virtual HR Interview Foundation

The interview feature is split into routes, Pydantic schemas, SQLAlchemy models, and services. `interview_sessions`, `interview_questions`, and `interview_answers` are created with the project's non-destructive development `create_all` mechanism. Session status and interview configuration use enums and server-side validation. Foreign keys attach sessions to users, questions to sessions, and answers to questions. Future `resume_id` and `company_id` relationships can be added when those tables exist; no placeholder foreign keys are created now.

Virtual HR profiles are static configuration in `backend/app/services/interviewers.py`, not a database table. The authenticated setup screen reads that catalogue through the interviewers API. It contains SIRI (friendly, supportive female Virtual HR) and Alex (structured, challenging male Virtual HR). Both are clearly presented as AI virtual interviewers, and the supplied portraits are mapped by profile ID in `frontend/src/config/virtualHrAvatars.js`.

Setup collects optional stored company context or a free-text company label, a job role, experience level, interview type, difficulty, duration, Virtual HR selection, and text/voice response preference. A summary is shown before the session starts. The general question engine is unchanged and does not consume company context.

The session lifecycle persists `in_progress`, `paused`, and `completed` states, timestamps, timer seconds, current question, and all submitted answers. The pause endpoint toggles between paused and in-progress. The browser countdown derives from persisted server timing and completion preserves previously submitted answers. Interview history and detail pages show only the authenticated user’s real sessions.

Questions are selected deterministically from a small general practice bank. They are tagged by category and saved with the requested difficulty, do not repeat within a session, and respect the selected interview type. The question wording is not difficulty-calibrated yet. These are practice prompts, not company-specific questions. The starter bank is finite; a session can end its question set before its chosen timer runs out.

Text mode is always available. Voice mode uses browser Web Speech recognition only where supported; permission denial, missing microphone, network errors, and unsupported browsers show a text fallback. Interview questions can be read aloud through browser SpeechSynthesis where available, with replay and stop controls. Browser voice support depends on the user’s browser and permissions.

At Phase 4 completion, `ai_service.py` was an unavailable provider boundary and sessions used deterministic practice questions. Phase 8 now adds the optional provider integration documented below; when it is not configured, the deterministic flow remains available and no AI feedback is shown.

> Phase 4 provides the interview-session foundation. Advanced adaptive AI questioning, answer evaluation, contextual follow-ups, and final AI reports remain future work. Phase 5 associates optional resume context with a session, and Phase 6 adds optional company context; the general question engine does not consume either context yet.

## Phase 5 — Resume Intelligence

The authenticated `/resume` page accepts PDF files only, with a 10 MB limit, drag-and-drop or file browsing, upload progress, replacement by uploading another document, a privacy notice, and a list of previously uploaded resumes. Resume results are available at `/resume/{id}`. Users can inspect and delete only their own files.

PDF content is validated and extracted with PyMuPDF. Server storage uses per-user directories and randomized names; the original name is sanitized and retained only as display metadata. The API never returns a filesystem path or the full extracted text. Empty or image-only PDFs are marked failed with a clear message; OCR is not enabled. The development storage root is `backend/storage/resumes` and should be protected with suitable filesystem permissions and backed up according to deployment policy.

The parser recognizes common section heading variants and produces contact fields, education, skills, projects, experience, certifications, achievements, and detected section text. Extracted skills remain separate from permanent user profile skills. Parsing is deterministic and template-independent but heuristic: fields such as institution, role, and project boundaries can require user review. `Resume Completeness` reports which structures were detected; it is not an ATS score or an objective resume-quality grade. Suggestions are rule-based. Project/skill-based practice questions are labeled as practice questions based on the resume and do not represent company questions.

Interview setup can optionally associate a processed resume with a new interview session; the session stores its resume ID and presents the filename in the room. The existing deterministic Phase 4 question engine does not yet use the resume to generate questions. The concise owned interview-context endpoint is available for a future integration. Deleting a resume clears the optional session reference where the database enforces its foreign key; existing SQLite databases receive an additive nullable column while retaining old sessions.

`resume_ai_service.py` defines a future provider boundary only. No AI provider is configured or called, and extraction results are kept distinct from any future AI suggestions.

> Resume Intelligence currently uses deterministic document extraction and structured analysis. Advanced semantic AI analysis, role-specific gap analysis, and AI-generated interview evaluation will be added in later phases.

Limitations: scanned PDFs need OCR in a future phase; the heuristic parser may miss or group fields on unusual layouts; MySQL schema behavior requires deployment migration planning and could not be verified here without credentials. The existing production startup does not auto-run development schema changes; apply the nullable `interview_sessions.resume_id` addition through a production migration before deploying this phase.

## Phase 6 — Company Intelligence

The authenticated `/company` directory supports case-insensitive search of stored company records. `/company/{id}` shows company overview fields, sources, technologies, roles, interview reports, and topics with verification labels. Missing information is explicitly marked unavailable. There is no seed dataset, no unrestricted company create/update API, and no special-case company behavior. Trusted ingestion is isolated in `company_service.ingest_company`; source URLs must be valid HTTP(S). No company facts have been added by this phase.

The research boundary in `company_research_service.py` reports unavailable until a provider is configured. `company_ai_service.py` is also an unavailable boundary. The knowledge trainer creates a deterministic practice question only from a stored founded year and a verified source; it hides the answer until submission and persists each signed-in user’s attempts. The trainer does not present questions as actual company interview questions.

Users can save private company bookmarks. Interview setup optionally selects a stored company and attaches `company_id` to the session while preserving free-text legacy company labels, optional resume association, and existing general interview questions. The interview context endpoint returns sourced structured fields and keeps verification statuses visible. Company deletion sets the optional interview relationship to null where the database schema supports foreign keys.

The supplied [placement preparation folder](https://drive.google.com/drive/u/0/folders/1NC5wLHUMUye5_5zHzSgTgXDUdVmh43ZU) is available as an external link. Its contents are not read or copied by the application. Configure a different authorized folder through `VITE_PLACEMENT_RESOURCES_URL` if needed. Phase 6 adds the company, sources, technology, role, interview insight/topic, bookmark, quiz question/attempt tables and nullable `interview_sessions.company_id`. Development startup creates new tables and applies the additive nullable column. Production startup does not run schema changes: apply an equivalent MySQL migration before deploying. MySQL was not available for verification.

## Phase 7 — Learning & Practice

The authenticated `/learning` hub offers Technical Preparation, HR Preparation, Aptitude Practice, Professional English, and Placement Resources. Categories and topics are database records, not just frontend labels. The seeded catalog includes the requested Python, SQL, DBMS, DSA, Web, Git, HR, aptitude, and English topics. Lesson content is concise and internally authored, with definitions, why it matters, explanations, examples, interview points, revision notes, and practice prompts. HR lessons provide flexible answer structures and avoid claiming one universally correct response.

Practice sessions use internal MCQ questions. The backend validates attempt ownership and question membership, hides correct answers before submission, calculates accuracy, persists answers, prevents duplicate submissions, and locks completed attempts. Accuracy is a summary of submitted practice answers, not a measure of overall knowledge. Topic completion is a separate explicit action. `learning_progress` tracks attempts, correct answers, practice accuracy, last practiced time, completion, and deterministic topic progress.

Recommendations use transparent rules: continue an incomplete topic, flag lower recent practice accuracy, then consider the saved career goal and processed resume skills, with a general placement fallback. Resume skills are only a recommendation signal, not evidence of proficiency. If a bookmarked company has sourced interview topics, those topics are shown with their verification status; absent company data stays clearly unavailable.

The Placement Resources hub searches stored resource records and links to the user-supplied Drive folder. No folder contents are assumed accessible, copied, or imported. The backend provider boundary reports import as unconfigured until a lawful connector or import mechanism is added. There are currently no seeded external resources or fabricated resource URLs.

Phase 7 creates `learning_categories`, `learning_topics`, `learning_resources`, `practice_questions`, `practice_attempts`, `practice_attempt_answers`, and `learning_progress`. Development startup creates the tables and idempotently seeds internal content. For an existing production database, back up and review the target first, run `python -m app.db.migrate_phase7` from `backend` to create only the Phase 7 tables, then run `python -m app.db.seed_learning` to add the internal catalog. Production startup does not run either command automatically. MySQL behavior was not exercised in this environment.

The `/learning/topic/{id}`, `/learning/practice`, `/learning/practice/{attempt_id}`, `/learning/history`, `/learning/english`, `/learning/aptitude`, and `/resources` routes share the existing authenticated app shell. Dashboard progress and recommended next steps are backed by the signed-in user's persisted records.

## Phase 8 — Advanced AI Interview

Virtual HR now supports an optional AI interview mode while preserving the rule-based practice question bank as its offline fallback. SIRI and Alex are application personas, not real recruiters. Setup collects the target role, interview type, difficulty mode, resume/company links, response mode, and interviewer. Adaptive difficulty changes only after multiple recent provider evaluations signal a consistent pattern; this is practice pacing, not an ability measurement.

`backend/app/services/ai_service.py` defines the provider interface and an OpenAI-compatible Chat Completions implementation. It is enabled only when backend `AI_PROVIDER` is `openai` or `openai_compatible`, and `AI_MODEL` plus `AI_API_KEY` are present. Optional `AI_BASE_URL` selects a compatible endpoint; it defaults to OpenAI's API. The API key is a backend `SecretStr`, never sent to the frontend, saved in the database, or included in status responses. No external provider is called by the automated tests. The UI shows provider availability and allows deterministic practice while AI is unavailable.

The provider generates one question at a time, evaluates a saved answer, may create up to two contextual follow-ups per primary question, and creates a final report only from saved evaluated answers. Each provider endpoint also requires that the candidate opted into AI Interview Mode for that session. Pydantic rejects malformed categories, difficulty values, missing data, extra output fields, non-finite values, and scores outside 0–10. Feedback dimensions are labeled as AI-generated practice feedback; they do not represent employability or hiring likelihood. Provider errors use bounded, secret-free messages; an answer is committed before the separate evaluation request so provider failure does not lose it. Failed evaluations can be retried.

Context builders limit resume facts to extracted skills, education, projects, experience, certifications, and achievements; personal contact fields and the full extracted resume text are excluded. Company context includes source-backed and verification-labeled information and describes public interview reports as publicly reported, not guaranteed procedure. Recent interview answers and learning-practice signals are bounded. Resume, company, and candidate-provided text is marked as untrusted input in dedicated prompt templates. No raw provider response is retained. Voice practice evaluates the saved browser transcript, not raw audio. The system does not assess personality, emotional state, accent, intelligence, hiring chance, or candidate rank.

Evaluations and final reports are stored in `interview_evaluations` and `interview_reports`; `interview_questions` records its source and parent for follow-ups. Session rows record the selected advanced interview type, AI mode, and current adaptive difficulty. New installations create these tables in development. For an existing production database, back up and review it, then run `python -m app.db.migrate_phase8` from `backend`. The migration adds defaulted fields and creates Phase 8 tables without dropping or rewriting existing interview answers. MySQL execution was not verified here.

The authenticated report page is available at `/interviews/{id}/report` and `/interview/{id}/report`. It shows only the saved provider report and per-answer evaluations; when no provider result exists, the page says so and offers a retry where eligible. Learning recommendations link to matching Phase 7 topics when found; sourced company trainer and resume-project practice suggestions appear only when supporting data exists.

## Phase 9 — Admin Dashboard

Administrators use a separate responsive console at `/admin`; candidate routes and navigation remain separate. Existing JWT authentication is reused. `users.role` is checked from the database on every authenticated request, so role changes and account deactivation apply immediately to subsequent API calls. Public registration always creates a `candidate`; there is no public admin registration or self-promotion endpoint. Active users means accounts with `is_active=true`.

Provision the first administrator from the trusted backend host. First register the intended account normally and complete startup so schema migrations have run, then use:

```powershell
cd backend
python -m app.db.provision_admin admin@example.com
```

The command only promotes an existing active account after an interactive password check. It does not create accounts or store a password in source control. Keep the backend shell and database access restricted. Further role changes are admin-only and audited. Admin role or active status changes cannot remove the last active administrator.

Admin APIs are under `/api/admin`: dashboard and aggregate analytics; paginated/searchable users with safe profile/activity summaries; source-backed company creation/update/deactivation, source verification, and sourced technology/role/topic management; learning category/topic/question management; platform resource management; interview aggregate statistics; and filtered audit logs. Company/resource URLs are restricted to HTTP(S). Company and learning/resource removal is a soft deactivate/unpublish operation to preserve user bookmarks, interview context, practice history, and progress. Practice questions are also unpublished rather than hard-deleted. Admin interview reporting returns counts only and never returns candidate answers or evaluation text. Audit metadata is allow-listed and excludes submitted content, credentials, tokens, and documents. Audit rows have no update/delete API.

`backend/app/db/migrations.py::ensure_phase9_admin_schema` adds a defaulted candidate role to existing users and creates `admin_activity_logs` without dropping data. Development startup applies this additive migration. For production, back up the database, review and run `python -m app.db.migrate_phase9` from `backend` as part of the controlled schema rollout before deploying; production startup does not auto-migrate. SQLite migration and API behavior are covered by tests. MySQL migration behavior was not verified. This phase does not add upload support; resources use existing records and safe external links, and private Drive content is not imported.

Run regression tests from `backend` with `python -m pytest -q -p no:cacheprovider -p no:tmpdir tests`; run the frontend build from `frontend` with `npm run build`. Phase 10 adds editable admin forms, question management, and in-app confirmation dialogs.

## Phase 10 — Testing & Security Hardening

The Phase 1–9 baseline before Phase 10 changes was 60 passing backend tests, Python bytecode compilation success, and a successful Vite production build. The final backend regression run passes 65 tests. Python compilation and the final frontend production build pass; the test run emits five upstream PyMuPDF/SWIG deprecation warnings.

Security review and regression coverage include password hashing and JWT validation (expired, malformed, and disallowed algorithm tokens), live database role checks, administrative provisioning, owner-scoped records, migrations, resume upload and privacy boundaries, AI provider failure sanitization and untrusted prompt context, interview flows, company data, learning practice, and dashboard data. Resume detail responses no longer include parsed section text or storage metadata. Validation errors omit submitted input values, and authentication/profile database errors no longer log bound values such as password hashes. Unexpected AI adapter exceptions map to a generic provider error. Admin editing and resume deletion use accessible in-app confirmation dialogs, including environments that block browser-native prompts. Frontend source has no `dangerouslySetInnerHTML` use or embedded provider credentials.

Browser checks used disposable local test data in SQLite. Candidate dashboard, resume, company, learning, interview list, and interview setup routes, along with all admin routes, were checked at 1366×768, 768×1024, and 390×844; admin routes were also checked at 1920×1080. No document-level horizontal overflow remained at those sizes. The browser test found and led to a fix for unsupported native prompt dialogs in admin create/edit actions; the new in-app company form was submitted successfully to the disposable database. Admin create/edit and destructive actions now use labeled dialogs and explicit confirmation.

MySQL verification not performed because required database access/configuration was unavailable. No live AI provider was configured, so provider behavior was tested with mocks rather than external requests. This phase did not add rate limiting or server-side JWT revocation; access tokens remain in browser local storage and expire after 60 minutes. These existing limitations should be considered before production deployment.

## Phase 11 — Production Setup and Release 1.0.0

**Release status: PHASE 11 PREPARED — EXTERNAL DEPLOYMENT PENDING.** Production deployment prepared but not externally deployed because required deployment credentials/access were unavailable. No production URLs, TLS, MySQL connection, live AI provider, or host backups have been verified. This workspace has no configured Git remote, so it must be pushed to a private Git repository before a host can import it.

### Selected hosting layout

- **Frontend:** Netlify static site, using `frontend` as the base directory, `npm run build` as the build command, and `dist` as the publish directory. `frontend/public/_redirects` provides client-side route fallback. Set `VITE_API_BASE_URL` to the final HTTPS API origin plus `/api`, and optionally set `VITE_PLACEMENT_RESOURCES_URL`. These are public build-time settings; never place credentials in them. See [Netlify SPA rewrites](https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/).
- **Backend:** Railway service rooted at `/backend`, with build command `pip install -r requirements.txt` and start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set the health check path to `/api/ready`; `/api/health` is liveness and `/api/ready` checks database connectivity without disclosing database errors. Railway's public networking provisions managed TLS for its public domains; verify the final frontend and API URLs use HTTPS. See [Railway monorepo services](https://docs.railway.com/deployments/monorepo), [health checks](https://docs.railway.com/deployments/healthchecks), and [public networking](https://docs.railway.com/networking/public-networking).
- **Database:** Railway MySQL service, referenced privately from the backend as `DATABASE_URL=${{MySQL.MYSQL_URL}}`. The application normalizes its `mysql://` scheme to the installed PyMySQL driver. Keep database networking private. Railway describes its MySQL template as a MySQL container you operate, so configure and verify backups and upgrades yourself. See [Railway MySQL](https://docs.railway.com/databases/mysql) and [Railway variables](https://docs.railway.com/variables).
- **Resume files:** attach a Railway persistent volume to the backend at `/data`, then set `UPLOAD_STORAGE_PATH=/data/resumes`. The application continues to use randomized names, content/size validation, path checks, ownership checks, and authenticated download routes. Back up this volume separately from MySQL. A single attached filesystem volume is intended for one backend instance; use private object storage before scaling the API across instances.

### Manual deployment sequence

1. Create a private Git repository, add this project, and push the release branch. No remote is configured in the current workspace.
2. Create the Netlify site from that repository with base `frontend`, build `npm run build`, and publish `dist`. Record the assigned HTTPS site origin. Set `VITE_API_BASE_URL` to `https://<backend-domain>/api` before the final build.
3. Create Railway MySQL and a backend service for the same repository with root `/backend`. Add a persistent volume mounted at `/data`.
4. Add backend variables in Railway: `ENVIRONMENT=production`; `DATABASE_URL=${{MySQL.MYSQL_URL}}`; a unique random `JWT_SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`); `JWT_ALGORITHM=HS256`; `ACCESS_TOKEN_EXPIRE_MINUTES=60`; `FRONTEND_URL=https://<exact-netlify-origin>`; and `UPLOAD_STORAGE_PATH=/data/resumes`. Do not include a trailing route or wildcard in `FRONTEND_URL`. Leave all `AI_*` variables unset to keep AI disabled; to enable later, provide `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY` only through Railway's backend variables, and an HTTPS `AI_BASE_URL` if using a compatible endpoint. `PLACEMENT_RESOURCES_URL` is optional. `.env.example` is for local development only; `frontend/.env.production.example` documents public frontend placeholders.
5. Configure `/api/ready` as the Railway health check. Copy the assigned backend HTTPS domain into Netlify's `VITE_API_BASE_URL` as `https://<backend-domain>/api`, then trigger the frontend production build/deploy. Deploy the backend again after setting the exact Netlify origin if that value changed.
6. Before any schema change, back up the database and resume volume. From the backend service shell, run `python -m app.db.migrate_production` with `ENVIRONMENT=production` and the production database configured. This reviewed runner creates missing tables, applies the project's additive compatibility migrations, and idempotently seeds InterviewHub learning content. It refuses non-MySQL connections and is never run automatically at app startup. Verify readiness and candidate/admin flows on the deployed HTTPS site before announcing release.
7. Register the intended administrator through the application, then from the backend shell run `python -m app.db.provision_admin admin@example.com` with that account's email. Do not promote a shared or test account.

### Backup, restore, and rollback

No backup schedule is enabled by this project. In Railway, enable snapshots for both the MySQL data volume and the resume volume; use daily snapshots with at least a week of retention and weekly snapshots with at least a month of retention if available on the selected plan. Take a manual backup immediately before migrations and perform a restore drill into an isolated service. Railway documents volume backup scheduling and restore in its [backup guide](https://docs.railway.com/volumes/backups); confirm the controls and retention shown for your account before relying on them.

For recovery, pause writes, restore the database and resume-file volume from a coordinated snapshot to an isolated service, verify readiness and file access, then switch traffic only after validation. The application has no destructive down migrations. If an additive rollout fails, restore the pre-migration database snapshot and redeploy the previously working application version; retain the failed service for diagnosis. Never restore an unverified backup directly over the live database.

### Verification and known release limits

The production settings validator rejects weak/default JWT secrets, non-HTTPS or non-exact frontend origins, local/non-MySQL production databases, relative upload paths, and partial AI configuration. CORS only permits the configured frontend origin. The explicit migration runner is tested twice against a disposable SQLite database for idempotency and preservation; this is not evidence of MySQL compatibility. Backend error responses avoid returning readiness connection details. Vite production builds reject an HTTP API URL, and its unset production API fallback is same-origin `/api` rather than localhost.

The release requires a real host account, private Git remote, production MySQL, assigned HTTPS domains, and verification of host backup controls. Accordingly, **MySQL production verification pending because database access was unavailable.** No browser end-to-end checks against staging/production were possible because no deployment URL or account was provided. A live AI provider was not configured. JWTs remain in browser local storage, expire after 60 minutes, and have no server-side revocation or rate limiting; consider these documented security improvements before broad public use.

## Current limitations

- MySQL must be available and configured before the API can start successfully.
- Authentication uses bearer JWTs in localStorage; this foundation does not yet include refresh tokens, server-side revocation, rate limiting, or account recovery.
- Development migration is intentionally small and idempotent; Alembic is not configured yet.
- The local MySQL service was not exercised in this environment because application database credentials were unavailable; automated API tests use SQLite.
- Advanced semantic resume analysis, company research, Drive import, and external learning-resource curation remain future work.

## Upcoming phases

| Phase | Status |
|---|---|
| Phase 0 — Project Inspection | ✅ |
| Phase 1 — Project Foundation | ✅ |
| Phase 2 — Authentication & Profile | ✅ (SQLite API and browser-verified; MySQL credentials unavailable here) |
| Phase 3 — Dashboard & Core UX | ✅ (8 SQLite API tests, production build, and browser navigation/responsive checks passed) |
| Phase 4 — Virtual HR Foundation | ✅ (17 SQLite API tests, production build, and browser lifecycle/responsive checks passed) |
| Phase 5 — Resume Intelligence | ✅ (26 SQLite API tests and production build passed) |
| Phase 6 — Company Intelligence | ✅ (32 SQLite API tests and frontend production build passed; browser checked landing page and protected-route redirect; company directory has no seeded data) |
| Phase 7 — Learning & Practice | ✅ (41 SQLite API tests and frontend production build passed; browser checked landing page and protected learning-route redirect) |
| Phase 8 — Advanced AI | ✅ (53 SQLite API/provider-mock tests and frontend production build passed; browser checked public landing, protected-route redirect, and reachable tablet/mobile widths; no live provider or MySQL verification) |
| Phase 9 — Admin | ✅ (60 SQLite regression tests, Python compile checks, frontend production build, and unauthenticated `/admin` browser redirect passed; no MySQL verification) |
| Phase 10 — Testing & Security | ✅ (65 SQLite regression tests, Python compile check, frontend production build, security-focused regressions, signed-in admin create flow, and responsive candidate/admin route checks passed; no MySQL or live AI provider verification) |
| Phase 11 — Production setup and release | ✅ Prepared; external deployment pending (no deployment access, Git remote, production MySQL, or HTTPS host to verify) |
