"""
Pydantic model that mirrors shared/schema.json exactly.
This is the single source of truth Cherry (Role A) validates every
Claude response against before it ever reaches Nandu's backend.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List


class AnalysisResult(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    matched_skills: List[str]
    missing_skills: List[str]
    candidate_feedback: List[str]
    recruiter_summary: str

    @field_validator("matched_skills", "missing_skills")
    @classmethod
    def dedupe_and_clean(cls, v: List[str]) -> List[str]:
        seen = set()
        cleaned = []
        for item in v:
            item = item.strip()
            key = item.lower()
            if item and key not in seen:
                seen.add(key)
                cleaned.append(item)
        return cleaned

    @field_validator("candidate_feedback")
    @classmethod
    def feedback_not_empty(cls, v: List[str]) -> List[str]:
        if len(v) == 0:
            raise ValueError("candidate_feedback must contain at least one bullet")
        return v

    @field_validator("recruiter_summary")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("recruiter_summary must not be empty")
        return v
