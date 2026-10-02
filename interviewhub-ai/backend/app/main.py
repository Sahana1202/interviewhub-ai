import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, companies, dashboard, health, interviews, learning, profile, resumes, admin
from app.core.config import settings
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.db.migrations import ensure_interview_resume_column, ensure_onboarding_completed_column, ensure_interview_company_column, ensure_phase8_interview_columns, ensure_phase9_admin_schema
from app import models  # noqa: F401 - imports register model metadata before create_all
from app.services.learning_seed_service import seed_learning_catalog

IS_PRODUCTION = settings.environment.lower() == "production"
logging.basicConfig(level=logging.INFO if IS_PRODUCTION else logging.DEBUG)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Safe for local development: creates missing tables and never drops existing data.
    if not IS_PRODUCTION:
        Base.metadata.create_all(bind=engine)
        ensure_onboarding_completed_column(engine)
        ensure_interview_resume_column(engine)
        ensure_interview_company_column(engine)
        ensure_phase8_interview_columns(engine)
        ensure_phase9_admin_schema(engine)
        with SessionLocal() as db:
            seed_learning_catalog(db)
    yield


app = FastAPI(title=f"{settings.app_name} API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_without_input_echo(_: Request, exc: RequestValidationError):
    # Pydantic v2 includes the rejected input by default; that can reflect passwords or private text.
    safe_errors = [{key: value for key, value in error.items() if key not in {"input", "ctx", "url"}}
                   for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": safe_errors})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(interviews.router, prefix="/api")
app.include_router(interviews.ai_router, prefix="/api")
app.include_router(resumes.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(learning.learning_router, prefix="/api")
app.include_router(learning.practice_router, prefix="/api")
app.include_router(learning.resources_router, prefix="/api")
app.include_router(admin.router, prefix="/api")
