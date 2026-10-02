import os
import re
import uuid
from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.resume import Resume

MAX_RESUME_BYTES = 10 * 1024 * 1024
STORAGE_ROOT = settings.upload_storage_path

SECTION_ALIASES = {
    "summary": {"summary", "professional summary", "profile", "objective", "career objective", "about me"},
    "education": {"education", "academic background", "educational qualification", "academic qualifications", "education qualification"},
    "skills": {"skills", "technical skills", "technical expertise", "core competencies", "key skills", "skills and technologies"},
    "experience": {"experience", "work experience", "professional experience", "employment history", "internship experience"},
    "projects": {"projects", "academic projects", "personal projects", "project experience", "key projects"},
    "certifications": {"certifications", "certificates", "licenses and certifications"},
    "achievements": {"achievements", "awards", "honors", "accomplishments"},
}
SKILL_TERMS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "React", "Angular", "Vue", "Node.js", "Express",
    "FastAPI", "Django", "Flask", "HTML", "CSS", "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Git",
    "GitHub", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Linux", "REST API", "Machine Learning", "TensorFlow",
    "PyTorch", "Pandas", "NumPy", "Power BI", "Tableau", "Figma", "Excel", "C", "Go", "Rust", "Spring Boot",
]


def normalize_text(value: str) -> str:
    value = value.replace("\x00", " ").replace("\r", "\n")
    value = re.sub(r"[\t\u00a0 ]+", " ", value)
    value = re.sub(r"\n[ \t]+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def split_sections(text: str) -> dict[str, str]:
    aliases = {re.sub(r"[^a-z0-9 ]", "", a.lower()): key for key, vals in SECTION_ALIASES.items() for a in vals}
    sections: dict[str, list[str]] = {"other": []}
    current = "other"
    for raw in text.splitlines():
        line = raw.strip(" •●▪-*\t")
        key = re.sub(r"[^a-z0-9 ]", "", line.lower()).strip()
        key = re.sub(r"\s+", " ", key)
        if key.endswith(":"):
            key = key[:-1].strip()
        if key in aliases:
            current = aliases[key]
            sections.setdefault(current, [])
        elif line:
            sections.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items() if lines}


def extract_contact(text: str) -> dict:
    email = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, re.I)
    phone = next((match for match in re.finditer(r"(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)", text)
                  if 10 <= len(re.sub(r"\D", "", match.group(0))) <= 15), None)
    urls = re.findall(r"(?:https?://|www\.)[^\s|,<>]+|(?:linkedin\.com|github\.com)/[^\s|,<>]+", text, re.I)
    urls = [url.rstrip(".)]}>") for url in urls]
    linkedin = next((url for url in urls if "linkedin.com" in url.lower()), None)
    github = next((url for url in urls if "github.com" in url.lower()), None)
    portfolio = next((url for url in urls if "linkedin.com" not in url.lower() and "github.com" not in url.lower()), None)
    first_lines = [line.strip() for line in text.splitlines() if line.strip()][:5]
    name = next((line for line in first_lines if re.fullmatch(r"[A-Z][A-Za-z.' -]{1,70}", line) and "@" not in line), None)
    return {"name": name, "email": email.group(0) if email else None,
            "phone": phone.group(0).strip() if phone else None, "linkedin": linkedin,
            "github": github, "portfolio": portfolio}


def extract_skills(sections: dict[str, str], text: str) -> list[str]:
    source = sections.get("skills", "")
    if not source:
        return []
    found = []
    for skill in SKILL_TERMS:
        if re.search(rf"(?<![\w+#.]){re.escape(skill)}(?![\w+#.])", source, re.I):
            found.append(skill)
    # Keep only explicit skill-section mentions; the full text is accepted for parser evolution.
    del text
    return found


def _lines(sections: dict[str, str], section: str) -> list[str]:
    return [line.strip(" •●▪-*\t") for line in sections.get(section, "").splitlines() if line.strip(" •●▪-*\t")]


def extract_education(sections: dict[str, str]) -> list[dict]:
    entries = []
    for line in _lines(sections, "education"):
        year = re.search(r"\b(?:19|20)\d{2}(?:\s*[-–]\s*(?:(?:19|20)\d{2}|present))?\b", line, re.I)
        score = re.search(r"\b(?:CGPA|GPA|percentage|score)\s*[:=-]?\s*\d+(?:\.\d+)?\s*%?", line, re.I)
        degree = re.search(r"\b(B\.?\s?Tech|M\.?\s?Tech|B\.?\s?E|M\.?\s?E|B\.?\s?Sc|M\.?\s?Sc|BCA|MCA|MBA|Bachelor(?:'s)?|Master(?:'s)?|Ph\.?D)\b[^,;|]*", line, re.I)
        parts = [part.strip() for part in re.split(r"[|,;]\s*", line) if part.strip()]
        institution = next((part for part in parts if not re.search(r"\b(B\.?\s?Tech|M\.?\s?Tech|B\.?\s?E|M\.?\s?E|B\.?\s?Sc|M\.?\s?Sc|BCA|MCA|MBA|Bachelor|Master|Ph\.?D)\b|\b(?:19|20)\d{2}\b|\b(?:CGPA|GPA|percentage|score)\b", part, re.I)), None)
        entries.append({"institution": institution, "degree": degree.group(0).strip() if degree else None,
                        "department": None, "graduation_year": year.group(0) if year else None,
                        "grade": score.group(0) if score else None})
    return entries


def extract_projects(sections: dict[str, str]) -> list[dict]:
    lines = _lines(sections, "projects")
    result = []
    for line in lines:
        technologies = [skill for skill in SKILL_TERMS if re.search(rf"(?<![\w+#.]){re.escape(skill)}(?![\w+#.])", line, re.I)]
        pieces = re.split(r"\s[-–—:]\s", line, maxsplit=1)
        name = pieces[0].strip()[:160]
        description = pieces[1].strip() if len(pieces) > 1 else line
        result.append({"name": name, "description": description, "technologies": technologies})
    return result


def extract_experience(sections: dict[str, str]) -> list[dict]:
    result = []
    for line in _lines(sections, "experience"):
        dates = re.search(r"\b(?:19|20)\d{2}(?:\s*[-–]\s*(?:(?:19|20)\d{2}|present))?\b", line, re.I)
        role_org = re.search(r"(?P<role>.+?)\s+(?:at|@)\s+(?P<organization>[^,|]+)", line, re.I)
        organization = role_org.group("organization").strip() if role_org else None
        if organization:
            if dates:
                organization = organization.replace(dates.group(0), "")
            organization = re.split(r"\s[-–—]\s", organization, maxsplit=1)[0].strip(" ,-") or None
        result.append({"organization": organization,
                       "role": role_org.group("role").strip() if role_org else line,
                       "dates": dates.group(0) if dates else None, "description": line})
    return result


def parse_resume(text: str) -> dict:
    sections = split_sections(text)
    certifications = _lines(sections, "certifications")
    achievements = _lines(sections, "achievements")
    projects = extract_projects(sections)
    experience = extract_experience(sections)
    education = extract_education(sections)
    skills = extract_skills(sections, text)
    links = any(extract_contact(text)[key] for key in ("linkedin", "github", "portfolio"))
    present = {
        "contact": bool(extract_contact(text).get("email") or extract_contact(text).get("phone")),
        "education": bool(education), "skills": bool(skills), "projects": bool(projects),
        "experience": bool(experience), "certifications": bool(certifications), "links": links,
    }
    suggestions = []
    if not projects: suggestions.append("Consider adding 1–3 relevant projects with technologies and outcomes.")
    if not links: suggestions.append("Consider adding a relevant project portfolio link.")
    if not experience: suggestions.append("If you have internship, freelance, academic, or relevant practical experience, consider documenting it clearly.")
    if not skills: suggestions.append("Consider listing relevant skills in a clearly labeled skills section.")
    questions = []
    for project in projects:
        questions.extend([
            f"Explain the architecture of your {project['name']} project.",
            f"What technologies did you use in {project['name']} and why?",
            f"What was the most challenging part of {project['name']}?",
        ])
    for skill in skills[:5]:
        questions.append(f"How have you used {skill} in a project or practical setting?")
    return {
        "contact": extract_contact(text), "education": education, "skills": skills,
        "projects": projects, "experience": experience, "certifications": certifications,
        "achievements": achievements, "sections": sections,
        "completeness": {"checks": present, "present_count": sum(present.values()), "total_checks": len(present)},
        "suggestions": suggestions, "practice_questions": questions,
    }


def extract_pdf(data: bytes) -> tuple[str, str | None]:
    try:
        with fitz.open(stream=data, filetype="pdf") as document:
            text = normalize_text("\n".join(page.get_text("text") for page in document))
    except Exception as exc:
        raise HTTPException(status_code=422, detail="We couldn't process this resume. Please try another PDF.") from exc
    if len(re.sub(r"\s", "", text)) < 20:
        return "", "This PDF appears to be scanned or image-based. Text extraction was not available."
    return text, None


async def read_upload(upload: UploadFile) -> tuple[bytes, str]:
    filename = Path(upload.filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Please upload a PDF file.")
    data = await upload.read(MAX_RESUME_BYTES + 1)
    if len(data) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="This file is larger than the 10 MB limit.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="Please upload a valid PDF file.")
    safe_name = re.sub(r"[^A-Za-z0-9._ ()-]", "_", filename).strip(" .")[:255] or "resume.pdf"
    return data, safe_name


def save_resume(db: Session, user_id: int, filename: str, data: bytes) -> Resume:
    text, message = extract_pdf(data)
    stored = f"{uuid.uuid4().hex}.pdf"
    folder = (STORAGE_ROOT / str(user_id)).resolve()
    root = STORAGE_ROOT.resolve()
    if not folder.is_relative_to(root):
        raise HTTPException(status_code=400, detail="Invalid storage location")
    if os.name != "nt":
        STORAGE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(STORAGE_ROOT, 0o700)
        os.chmod(folder, 0o700)
    else:
        STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
        folder.mkdir(parents=True, exist_ok=True)
    path = (folder / stored).resolve()
    if not path.is_relative_to(folder):
        raise HTTPException(status_code=400, detail="Invalid storage location")
    with path.open("xb") as stored_file:
        stored_file.write(data)
    if os.name != "nt":
        os.chmod(path, 0o600)
    resume = Resume(user_id=user_id, file_name=filename, stored_file_name=stored, file_path=str(path),
                    file_size=len(data), mime_type="application/pdf", extracted_text=text or None,
                    parsed_data=parse_resume(text) if text else {}, status="failed" if message else "processed",
                    processing_message=message)
    try:
        db.add(resume)
        db.commit()
        db.refresh(resume)
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return resume


def owned_resume(db: Session, user_id: int, resume_id: int) -> Resume:
    resume = db.scalar(select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id))
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


def delete_resume(db: Session, resume: Resume) -> None:
    root = STORAGE_ROOT.resolve()
    path = Path(resume.file_path).resolve()
    owner_folder = (root / str(resume.user_id)).resolve()
    if path.parent == owner_folder and path.name == resume.stored_file_name and path.is_relative_to(root):
        path.unlink(missing_ok=True)
    db.delete(resume)
    db.commit()
