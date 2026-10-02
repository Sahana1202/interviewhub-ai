from functools import lru_cache
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    app_name: str = "InterviewHub AI"
    environment: str = "development"
    database_url: SecretStr = SecretStr("mysql+pymysql://username:password@localhost:3306/interviewhub")
    jwt_secret_key: SecretStr = SecretStr("replace_with_a_long_random_secret_before_use")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    frontend_url: str = "http://localhost:5173"
    upload_storage_path: Path = Path(__file__).resolve().parents[2] / "storage" / "resumes"
    placement_resources_url: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_api_key: SecretStr | None = None
    ai_base_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def require_production_secret(self) -> "Settings":
        if self.environment.lower() == "production":
            secret = self.jwt_secret_key.get_secret_value()
            if secret == "replace_with_a_long_random_secret_before_use" or len(secret) < 32:
                raise ValueError("Set a unique JWT_SECRET_KEY of at least 32 characters in production")
            try:
                database = make_url(self.database_url.get_secret_value())
            except Exception:
                raise ValueError("Production DATABASE_URL must be a valid credentialed MySQL URL") from None
            if database.drivername != "mysql+pymysql" or not database.host or not database.username or not database.password:
                raise ValueError("Production requires a credentialed MySQL DATABASE_URL using the PyMySQL driver")
            if database.username == "username" or database.host.lower() in {"localhost", "127.0.0.1"}:
                raise ValueError("Production DATABASE_URL must point to the configured remote database")
            frontend = urlparse(self.frontend_url)
            if (frontend.scheme != "https" or not frontend.hostname or frontend.hostname == "*" or
                    frontend.path not in {"", "/"} or frontend.query or frontend.fragment or frontend.username):
                raise ValueError("Production FRONTEND_URL must be one exact HTTPS origin")
            portable_upload_path = str(self.upload_storage_path).replace("\\", "/")
            if not self.upload_storage_path.is_absolute() and not PurePosixPath(portable_upload_path).is_absolute():
                raise ValueError("Production UPLOAD_STORAGE_PATH must be an absolute persistent-storage path")
            ai_configured = bool((self.ai_provider or "").strip() or (self.ai_model or "").strip() or
                                 (self.ai_api_key and self.ai_api_key.get_secret_value().strip()))
            if ai_configured and not (self.ai_provider and self.ai_model and self.ai_api_key and
                                      self.ai_api_key.get_secret_value().strip()):
                raise ValueError("Configure AI_PROVIDER, AI_MODEL, and AI_API_KEY together, or leave AI disabled")
            if ai_configured and self.ai_base_url and urlparse(self.ai_base_url).scheme != "https":
                raise ValueError("Production AI_BASE_URL must use HTTPS")
        return self

    @field_validator("database_url", mode="before")
    @classmethod
    def use_pymysql_driver(cls, value: str | SecretStr) -> str:
        # Railway's MYSQL_URL uses mysql://; SQLAlchemy should use the already-installed PyMySQL driver.
        if isinstance(value, SecretStr):
            value = value.get_secret_value()
        if isinstance(value, str) and value.startswith("mysql://"):
            return "mysql+pymysql://" + value.removeprefix("mysql://")
        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def supported_jwt_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("This foundation currently supports HS256 JWT signing only")
        return value

    @field_validator("access_token_expire_minutes")
    @classmethod
    def positive_expiry(cls, value: int) -> int:
        if value < 1:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
