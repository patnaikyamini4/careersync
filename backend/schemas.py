from pydantic import BaseModel, Field


# =========================================================
# ANALYSIS RESULT
# =========================================================

class AnalysisResult(BaseModel):

    match_score: int = Field(
        ge=0,
        le=100,
        description="Resume-job match score from 0 to 100",
    )

    matched_skills: list[str]

    missing_skills: list[str]

    candidate_feedback: list[str]

    recruiter_summary: str


# =========================================================
# HEALTH STATUS
# =========================================================

class HealthStatus(BaseModel):

    status: str

    demo_mode: bool

    extraction_live: bool

    analysis_live: bool

    analysis_provider: str