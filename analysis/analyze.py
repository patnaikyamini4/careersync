"""
Role A (Cherry) — Analysis engine, FREE-TIER VERSION using Google Gemini.

Uses the current `google-genai` SDK (package: google-genai,
import path: `from google import genai`).

Same public contract as before, so nothing downstream changes:
    analyze_resume(resume_text: str, jd_text: str) -> dict

Setup:
  1. Go to https://aistudio.google.com/apikey
  2. Sign in with a Google account, click "Create API key" — no card required
  3. Put it in analysis/.env as:
       GEMINI_API_KEY=your-key-here
  4. pip install -r requirements.txt
"""

import os
import re
import time
import json
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import ValidationError

from schema import AnalysisResult

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Stable, production model as of Aug 2026. If this 404s later (Google moves
# fast), check https://ai.google.dev/gemini-api/docs/models for the current
# stable model id and swap it here — nothing else in this file needs to change.
MODEL = "gemini-3.6-flash"
PROVIDER = "gemini"

SYSTEM_PROMPT = """You are an expert technical recruiter and resume coach evaluating \
a candidate's resume against a specific job description.

Return ONLY a single JSON object — no markdown code fences, no preamble, no \
explanation before or after it. It must match exactly this schema:

{
  "match_score": <int 0-100>,
  "matched_skills": [<string>, ...],
  "missing_skills": [<string>, ...],
  "candidate_feedback": [<string>, ...],
  "recruiter_summary": "<string>"
}

Rules:
1. match_score reflects overall fit against the JD's requirements, weighted \
toward must-have qualifications over nice-to-haves. Be honest, not generous —
a resume with no overlap should score low (under 30), not a default ~50.
2. matched_skills: only skills/tools/technologies that appear (or are clearly \
and specifically implied, e.g. "built REST APIs in Flask" implies REST APIs) \
in BOTH the resume and the JD. Deduplicate, normalize casing/naming \
(e.g. "Postgres" not "postgresql/Postgres").
3. missing_skills: only skills the JD explicitly requires or strongly implies \
that are absent from the resume. Never invent skills the JD never mentioned.
4. candidate_feedback: 3-5 bullets. Each must reference a concrete, specific \
resume element (a bullet point's content, a section, a skill placement) — never \
generic advice like "improve formatting" or "add more detail" with nothing to \
anchor it. Feedback should be immediately actionable.
5. recruiter_summary: 1-2 plain sentences a recruiter can skim in 5 seconds.
6. EDGE CASE — short/thin resume (roughly under 150 words of real content, or \
missing most sections): still return fully valid JSON. Set match_score \
conservatively low, keep matched_skills honest (don't guess), and make one \
candidate_feedback bullet specifically ask for the missing sections/detail \
rather than fabricating an assessment.
7. EDGE CASE — zero overlapping skills: return an empty matched_skills list \
(never fabricate a match), and say so plainly in recruiter_summary.
8. Never include any text outside the JSON object.
9. Keep candidate_feedback bullets concise (under ~25 words each) so the full \
response fits comfortably within the output limit.
"""

GENERATE_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    max_output_tokens=2048,  # raised from 1024 — thin_resume case worked,
    # strong_match/partial_match were getting cut off mid-JSON on longer,
    # more detailed feedback.
    # NOTE: temperature/top_p/top_k are deprecated and ignored (or error)
    # on gemini-3.6-flash and later — don't set them here.
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def _extract_json(text: str) -> str:
    """Strip markdown fences / stray text the model sometimes wraps JSON in."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


def _call_model(resume_text: str, jd_text: str, repair_note: Optional[str] = None) -> str:
    user_content = f"RESUME:\n{resume_text}\n\nJOB DESCRIPTION:\n{jd_text}"
    if repair_note:
        user_content = f"{repair_note}\n\n{user_content}"

    response = client.models.generate_content(
        model=MODEL,
        contents=user_content,
        config=GENERATE_CONFIG,
    )
    return response.text


def analyze_resume(resume_text: str, jd_text: str, max_retries: int = 3) -> dict:
    """
    Single entrypoint. Nandu imports this straight into the FastAPI endpoint:
        from analyze import analyze_resume
        result = analyze_resume(resume_text, job_description)

    Always returns a dict matching shared/schema.json, or raises RuntimeError
    after exhausting retries (backend should catch this and return a 502/500).

    Retries two distinct failure modes differently:
      - Invalid/truncated JSON or schema mismatch -> repair prompt, no wait
        (the model just needs to be told what was wrong).
      - Transient API errors (503 overloaded, network blips) -> plain retry
        with a short exponential backoff, no repair prompt needed.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text is empty — check Ankitha's extraction step upstream.")
    if not jd_text or not jd_text.strip():
        raise ValueError("jd_text is empty.")

    last_error = None
    repair_note = None

    for attempt in range(max_retries + 1):
        try:
            raw = _call_model(resume_text, jd_text, repair_note)
        except Exception as e:
            # Transient server-side error (e.g. 503 UNAVAILABLE) — back off
            # and retry with the same prompt, no repair note needed.
            last_error = e
            repair_note = None
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
            continue

        json_str = _extract_json(raw)
        try:
            parsed = json.loads(json_str)
            validated = AnalysisResult(**parsed)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            last_error = e
            repair_note = (
                "Your previous response was not valid JSON matching the required "
                f"schema (error: {e}). Keep feedback bullets concise so the response "
                "fits the output limit. Return ONLY the corrected JSON object, "
                "nothing else — no fences, no commentary."
            )
            continue

    raise RuntimeError(
        f"analyze_resume failed after {max_retries + 1} attempts. Last error: {last_error}"
    )


if __name__ == "__main__":
    sample_resume = """
    Priya Sharma — Backend Developer
    3 years experience building REST APIs in Python/Flask.
    Wrote SQL queries and optimized Postgres schemas for a fintech startup.
    Led migration of a monolith to microservices, deployed on AWS EC2.
    """
    sample_jd = """
    We're hiring a Backend Engineer. Must have: Python, REST API design,
    SQL/Postgres, Docker & Kubernetes experience, AWS. Nice to have: Go.
    """
    result = analyze_resume(sample_resume, sample_jd)
    print(json.dumps(result, indent=2))
