"""Explicit boundary for future semantic resume analysis providers."""


class ResumeAIUnavailable(RuntimeError):
    pass


class ResumeAIService:
    def analyze_resume(self, *_args, **_kwargs):
        raise ResumeAIUnavailable("AI resume analysis is not configured")

    def extract_semantic_skills(self, *_args, **_kwargs):
        raise ResumeAIUnavailable("AI resume analysis is not configured")

    def generate_resume_questions(self, *_args, **_kwargs):
        raise ResumeAIUnavailable("AI resume analysis is not configured")

    def identify_role_gaps(self, *_args, **_kwargs):
        raise ResumeAIUnavailable("AI resume analysis is not configured")
