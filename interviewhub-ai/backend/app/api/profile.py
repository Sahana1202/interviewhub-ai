import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.profile import OnboardingSubmission, ProfileResponse, ProfileUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])


def profile_response(profile: UserProfile) -> ProfileResponse:
    return ProfileResponse.model_validate(profile)


@router.get("", response_model=ProfileResponse)
def get_profile(user: User = Depends(get_current_user)) -> ProfileResponse:
    return profile_response(user.profile)


@router.put("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = user.profile
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)

    # A completed profile stays complete while its two required career fields remain present.
    if not profile.target_role or not profile.experience_level:
        profile.onboarding_completed = False

    try:
        db.commit()
        db.refresh(profile)
    except SQLAlchemyError:
        db.rollback()
        logger.error("Database error while updating user profile")
        raise HTTPException(status_code=503, detail="Profile could not be saved right now") from None
    return profile_response(profile)


@router.post("/onboarding", response_model=ProfileResponse)
def complete_onboarding(
    payload: OnboardingSubmission,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    profile = user.profile
    for field, value in payload.model_dump().items():
        setattr(profile, field, value)
    profile.onboarding_completed = True
    try:
        db.commit()
        db.refresh(profile)
    except SQLAlchemyError:
        db.rollback()
        logger.error("Database error while completing onboarding")
        raise HTTPException(status_code=503, detail="Profile could not be completed right now") from None
    return profile_response(profile)
