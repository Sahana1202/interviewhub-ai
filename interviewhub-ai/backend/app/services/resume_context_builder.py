"""Privacy-filtered resume context. Contact details and full extracted text are never included."""

MAX_RESUME_CONTEXT_CHARS = 6000


def build_resume_context(resume) -> dict:
    if not resume or resume.status != "processed":
        return {"available": False}
    data = resume.parsed_data or {}
    context = {
        "skills": (data.get("skills") or [])[:30],
        "education": [{key: row.get(key) for key in ("degree", "institution", "year") if row.get(key)} for row in (data.get("education") or [])[:5] if isinstance(row, dict)],
        "projects": [{key: row.get(key) for key in ("name", "description", "technologies", "role", "outcome") if row.get(key)} for row in (data.get("projects") or [])[:8] if isinstance(row, dict)],
        "experience": [{key: row.get(key) for key in ("role", "organization", "description", "duration") if row.get(key)} for row in (data.get("experience") or [])[:8] if isinstance(row, dict)],
        "certifications": (data.get("certifications") or [])[:8],
        "achievements": (data.get("achievements") or [])[:8],
    }
    bounded = str(context)[:MAX_RESUME_CONTEXT_CHARS]
    return {"available": True, "facts": bounded}
