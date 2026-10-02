"""Validated, optional OpenAI-compatible provider boundary for interview practice."""
import json
import urllib.error
import urllib.request
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, ValidationError

from app.core.config import Settings, settings
from app.prompts.interview_prompts import EVALUATION_SYSTEM, FOLLOWUP_SYSTEM, QUESTION_SYSTEM, REPORT_SYSTEM


class AIServiceUnavailable(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


class InterviewQuestionAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=8, max_length=1200)
    category: Literal["HR", "Technical", "Behavioral", "Situational", "Introduction", "Role Specific", "Project", "Resume", "Company", "Aptitude", "Communication"]
    difficulty: Literal["Beginner", "Intermediate", "Advanced"]
    question_type: Literal["HR", "Technical", "Behavioral", "Situational", "Introduction", "Role Specific", "Project", "Resume", "Company", "Aptitude", "Communication"]


class AnswerEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overall_feedback: str = Field(min_length=10, max_length=1500)
    strengths: list[Annotated[str, Field(min_length=2, max_length=300)]] = Field(max_length=6)
    areas_to_improve: list[Annotated[str, Field(min_length=2, max_length=300)]] = Field(max_length=6)
    technical_accuracy: FiniteFloat | None = Field(default=None, ge=0, le=10)
    relevance: FiniteFloat = Field(ge=0, le=10)
    clarity: FiniteFloat = Field(ge=0, le=10)
    completeness: FiniteFloat = Field(ge=0, le=10)
    follow_up_needed: bool


class FollowUpAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=8, max_length=1200)
    category: Literal["HR", "Technical", "Behavioral", "Situational", "Introduction", "Role Specific", "Project", "Resume", "Company", "Aptitude", "Communication"]
    difficulty: Literal["Beginner", "Intermediate", "Advanced"]
    question_type: Literal["HR", "Technical", "Behavioral", "Situational", "Introduction", "Role Specific", "Project", "Resume", "Company", "Aptitude", "Communication"]


class TopicRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str = Field(min_length=2, max_length=160)
    reason: str = Field(min_length=4, max_length=400)


class TopicBreakdownAI(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: str = Field(min_length=2, max_length=120)
    summary: str = Field(default="", max_length=500)
    evidence: str = Field(default="", max_length=600)


class FinalReportAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=10, max_length=2000)
    strengths: list[Annotated[str, Field(min_length=2, max_length=300)]] = Field(max_length=8)
    improvement_areas: list[Annotated[str, Field(min_length=2, max_length=300)]] = Field(max_length=8)
    topic_breakdown: list[TopicBreakdownAI] = Field(max_length=20)
    communication_feedback: str = Field(max_length=1200)
    technical_feedback: str = Field(max_length=1200)
    recommended_topics: list[TopicRecommendation] = Field(max_length=8)


def _parse_json(content: str) -> dict:
    value = content.strip()
    if value.startswith("```"):
        value = value.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("Provider response must be a JSON object")
    return parsed


class AIService:
    """Uses the Chat Completions JSON mode only when all backend secrets are configured."""
    def __init__(self, config: Settings | None = None, timeout_seconds: float = 20):
        self.config = config or settings
        self.timeout_seconds = timeout_seconds

    @property
    def available(self) -> bool:
        return (self.config.ai_provider or "").lower() in {"openai", "openai_compatible"} and bool(
            self.config.ai_model and self.config.ai_api_key and self.config.ai_api_key.get_secret_value().strip()
        )

    @property
    def provider(self) -> str | None:
        return (self.config.ai_provider or "openai_compatible") if self.available else None

    @property
    def model(self) -> str | None:
        return self.config.ai_model if self.available else None

    def status(self) -> dict:
        return {"available": self.available, "provider": self.provider, "model": self.model}

    def _chat(self, system_prompt: str, context: dict, response_model: type[BaseModel]):
        if not self.available:
            raise AIServiceUnavailable("AI interview features unavailable; no AI provider is configured. Please configure an AI provider.")
        base_url = (self.config.ai_base_url or "https://api.openai.com/v1").rstrip("/")
        body = json.dumps({
            "model": self.config.ai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.4,
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url}/chat/completions", data=body, method="POST",
            headers={"Authorization": f"Bearer {self.config.ai_api_key.get_secret_value()}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read(256_000))
            content = payload["choices"][0]["message"]["content"]
            return response_model.model_validate(_parse_json(content))
        except urllib.error.HTTPError as exc:
            # Do not retain or return provider response bodies, which may include sensitive metadata.
            if exc.code == 429:
                raise AIProviderError("AI provider is temporarily rate limited.") from None
            if exc.code in {401, 403}:
                raise AIProviderError("AI provider authentication failed. Check backend configuration.") from None
            raise AIProviderError("AI provider could not complete this request.") from None
        except (TimeoutError, urllib.error.URLError):
            raise AIProviderError("AI provider timed out or could not be reached.") from None
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValidationError, ValueError):
            raise AIProviderError("AI provider returned an invalid response. Please retry.") from None
        except Exception:
            # Transport adapters may raise implementation-specific errors; never forward their details.
            raise AIProviderError("AI provider could not complete this request. Please retry.") from None

    def generate_question(self, context: dict | None = None) -> InterviewQuestionAIResponse:
        return self._chat(QUESTION_SYSTEM, context or {}, InterviewQuestionAIResponse)

    def evaluate_answer(self, context: dict | None = None) -> AnswerEvaluation:
        return self._chat(EVALUATION_SYSTEM, context or {}, AnswerEvaluation)

    def generate_followup(self, context: dict | None = None) -> FollowUpAIResponse:
        return self._chat(FOLLOWUP_SYSTEM, context or {}, FollowUpAIResponse)

    def generate_report(self, context: dict | None = None) -> FinalReportAIResponse:
        return self._chat(REPORT_SYSTEM, context or {}, FinalReportAIResponse)

