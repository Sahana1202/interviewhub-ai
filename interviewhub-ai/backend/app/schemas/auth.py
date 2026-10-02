from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    college: str | None = None
    degree: str | None = None
    department: str | None = None
    graduation_year: int | None = None
    experience_level: str | None = None
    target_role: str | None = None
    target_industry: str | None = None
    location: str | None = None
    onboarding_completed: bool = False


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str = "candidate"
    profile: ProfileResponse


class AuthResponse(TokenResponse):
    user: UserResponse
