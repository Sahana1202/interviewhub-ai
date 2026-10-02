"""Explicit unavailable AI boundary; Phase 6 uses deterministic, sourced content only."""


class CompanyAIUnavailable(RuntimeError):
    pass


def summarize_company(*_args, **_kwargs):
    raise CompanyAIUnavailable("Company AI provider unavailable.")


def generate_company_questions(*_args, **_kwargs):
    raise CompanyAIUnavailable("Company AI provider unavailable.")


def analyze_role_fit(*_args, **_kwargs):
    raise CompanyAIUnavailable("Company AI provider unavailable.")


def generate_company_interview_context(*_args, **_kwargs):
    raise CompanyAIUnavailable("Company AI provider unavailable.")
