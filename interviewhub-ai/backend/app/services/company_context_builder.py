"""Company context retains source-verification labels and bounds imported content."""

MAX_COMPANY_CONTEXT_CHARS = 3500


def build_company_context(db, company) -> dict:
    if not company:
        return {"available": False}
    from app.services.company_service import interview_context

    data = interview_context(db, company.id)
    trusted_topics = [item for item in data["reported_interview_topics"] + data["reported_hr_topics"]
                      if item.get("verification_status") in {"verified", "publicly_reported"}][:12]
    def public_source(item):
        source = item.get("source") or {}
        return (item.get("verification_status") in {"verified", "publicly_reported"}
                or source.get("verification_status") in {"verified", "publicly_reported"})

    facts = {
        "company_name": data["company_name"],
        "overview": data["overview"],
        "technologies": [item for item in data["technologies"] if public_source(item)][:12],
        "roles": [item for item in data["roles"] if public_source(item)][:8],
        "publicly_reported_interview_topics": trusted_topics,
    }
    return {"available": True, "facts": str(facts)[:MAX_COMPANY_CONTEXT_CHARS],
            "label": "Publicly reported information only; not a guarantee of company procedure."}
