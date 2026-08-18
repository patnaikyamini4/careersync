"""
structure.py — Role B (Ankitha): plain resume text -> lightweight structured dict.

This is OPTIONAL extra signal, not the main contract. The handoff doc is
explicit that Cherry's Claude call (Role A) is much better at *interpreting*
resume text than a regex parser is at structuring it — so keep this cheap,
fast, and RAM-safe (no spaCy `en_core_web_lg`, no sentence-transformers).

Two ways to use it:
  1. Standalone signal for your own testing/demo ("look, we detect skills
     without even calling Claude").
  2. Optionally passed alongside raw text into analyze_resume() as a hint —
     confirm with Cherry (Role A) whether she wants this; the schema
     contract (shared/schema.json) doesn't require it, so don't block on it.
"""

from __future__ import annotations

import re
from typing import Optional

# A deliberately compact, high-precision skill list. Better to under-detect
# than to flood matched_skills with noise (e.g. "R" matching inside random
# words) — Claude's downstream analysis is where nuanced skill-matching
# actually happens, this is just a cheap first pass.
SKILL_KEYWORDS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "nosql",
    "mongodb", "postgresql", "mysql", "docker", "kubernetes", "aws", "azure",
    "gcp", "git", "react", "angular", "vue", "node.js", "django", "flask",
    "fastapi", "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn",
    "machine learning", "deep learning", "nlp", "computer vision",
    "rest apis", "graphql", "linux", "bash", "html", "css", "excel",
    "power bi", "tableau", "spark", "hadoop", "jenkins", "ci/cd", "agile",
    "scrum", "figma", "photoshop", "salesforce", "sap", "r", "matlab",
]

SECTION_PATTERNS = {
    "education": r"(education|academic background|qualifications)",
    "experience": r"(experience|employment history|work history|professional experience)",
    "skills": r"(skills|technical skills|core competencies)",
    "projects": r"(projects|personal projects|key projects)",
    "certifications": r"(certifications?|licenses?)",
}

EMAIL_RE = re.compile(r"[\w\.\-+]+@[\w\-]+\.[\w\.\-]+")
PHONE_RE = re.compile(r"(\+?\(?\d{3}\)?[\d\-\.\s]{7,}\d)")
LINKEDIN_RE = re.compile(r"(linkedin\.com/in/[\w\-]+)", re.IGNORECASE)


def extract_contact(text: str) -> dict:
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    linkedin = LINKEDIN_RE.search(text)
    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0).strip() if phone else None,
        "linkedin": linkedin.group(0) if linkedin else None,
    }


def extract_skills(text: str) -> list[str]:
    """Case-insensitive substring match against SKILL_KEYWORDS. Word-boundary
    aware so 'r' doesn't match inside 'career'."""
    text_lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(found)


def split_sections(text: str) -> dict[str, str]:
    """Best-effort split of resume text into named sections based on common
    header phrases. Degrades gracefully: if no headers are found, everything
    lands under 'body' rather than raising."""
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"body": []}
    current = "body"

    for line in lines:
        stripped = line.strip()
        matched_section: Optional[str] = None
        # Header lines are usually short, so avoid matching a paragraph that
        # happens to contain the word "experience" mid-sentence.
        if 0 < len(stripped) <= 40:
            for name, pattern in SECTION_PATTERNS.items():
                if re.fullmatch(pattern, stripped, re.IGNORECASE):
                    matched_section = name
                    break
        if matched_section:
            current = matched_section
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {name: "\n".join(chunk).strip() for name, chunk in sections.items() if "\n".join(chunk).strip()}


def parse_resume_structured(text: str) -> dict:
    """Full lightweight structured pass. This is what you can log/print for
    your own Day-1 testing to sanity-check extraction quality before it
    ever reaches Cherry's Claude call."""
    if not text or not text.strip():
        return {"contact": {"email": None, "phone": None, "linkedin": None},
                "skills": [], "sections": {}}

    return {
        "contact": extract_contact(text),
        "skills": extract_skills(text),
        "sections": split_sections(text),
    }


if __name__ == "__main__":
    import json
    import sys

    from extract import extract_resume_text

    if len(sys.argv) != 2:
        print("Usage: python structure.py <path_to_resume.pdf|.docx>")
        sys.exit(1)

    raw_text = extract_resume_text(sys.argv[1])
    result = parse_resume_structured(raw_text)
    print(json.dumps(result, indent=2))
