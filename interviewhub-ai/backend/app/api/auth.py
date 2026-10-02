import logging

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.profile import UserProfile
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise unauthorized
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise unauthorized from None
    user = db.scalar(select(User).options(joinedload(User.profile)).where(User.id == user_id))
    if user is None or not user.is_active:
        raise unauthorized
    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name cannot be blank")
    user = User(name=name, email=str(payload.email).lower(), password_hash=hash_password(payload.password))
    user.profile = UserProfile()
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        db.refresh(user.profile)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    except SQLAlchemyError:
        db.rollback()
        logger.error("Database error while registering a user")
        raise HTTPException(status_code=503, detail="Registration is temporarily unavailable") from None
    return AuthResponse(access_token=create_access_token(str(user.id)), user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).options(joinedload(User.profile)).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect", headers={"WWW-Authenticate": "Bearer"})
    return AuthResponse(access_token=create_access_token(str(user.id)), user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
