from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ExperienceLevel = Literal["Student", "Fresher", "0–1 years", "1–3 years", "3+ years"]


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    college: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    graduation_year: int | None = Field(default=None, strict=True, ge=1950, le=date.today().year + 10)
    experience_level: ExperienceLevel | None = None
    target_role: str | None = Field(default=None, max_length=120)
    target_industry: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=160)

    @field_validator("college", "degree", "department", "target_role", "target_industry", "location")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("graduation_year")
    @classmethod
    def validate_graduation_year(cls, value: int | None) -> int | None:
        if value is not None and value > date.today().year + 10:
            raise ValueError("Enter a realistic graduation year")
        return value

    @field_validator("target_role", mode="before")
    @classmethod
    def require_nonblank_role(cls, value: object) -> object:
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("Enter a target role")
            return cleaned
        return value


class OnboardingSubmission(ProfileUpdate):
    experience_level: ExperienceLevel
    target_role: str = Field(min_length=2, max_length=120)


class ProfileResponse(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    onboarding_completed: bool = False

    @classmethod
    def from_profile(cls, profile: object) -> "ProfileResponse":
        return cls.model_validate(profile)
