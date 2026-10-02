"""Provider boundary for future lawful, source-backed company research integrations."""
from dataclasses import dataclass


class ResearchUnavailable(RuntimeError):
    pass


@dataclass
class CompanyResearchProvider:
    def search(self, query: str):
        raise ResearchUnavailable("Company research provider unavailable.")


def get_research_provider() -> CompanyResearchProvider:
    # No provider or credentials are configured in Phase 6.
    return CompanyResearchProvider()
