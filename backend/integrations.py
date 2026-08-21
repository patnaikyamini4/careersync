"""
Wires in Ankitha's extract_resume_text() and Cherry's analyze_resume().

Import is best-effort: if parsing/extract.py or analysis/analyze.py don't
exist yet (or DEMO_MODE is forced on), we fall back to mock functions that
satisfy the exact same contract. This means:
  - Nandu can build/test the full endpoint on hour 1, before B/A finish.
  - Padmini can point her frontend at a live backend immediately.
  - If a live Claude call misbehaves right before the pitch, DEMO_MODE=true
    guarantees the demo still works end to end.

extraction_live / analysis_live are exposed for the /health endpoint so the
Day-1-hour-8 sync check ("B's extraction + A's Claude call both work
standalone") has something concrete to look at instead of Slack messages.
"""
import itertools
import json
import logging
import sys
from pathlib import Path

from config import PARSING_DIR, ANALYSIS_DIR, DEMO_MODE, FIXTURES_DIR

logger = logging.getLogger("careersync.integrations")

extraction_live = False
analysis_live = False
analysis_provider = "mock"


def _load_fixtures() -> list[dict]:
    if not FIXTURES_DIR.exists():
        return []
    fixtures = []
    for p in sorted(FIXTURES_DIR.glob("*.json")):
        try:
            fixtures.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception as e:
            logger.warning("Skipping bad fixture %s: %s", p.name, e)
    return fixtures


_fixtures = _load_fixtures()
_fixture_cycle = itertools.cycle(_fixtures) if _fixtures else None
if _fixtures:
    logger.info("Loaded %d captured demo fixtures from %s", len(_fixtures), FIXTURES_DIR)


# ---- mock fallbacks (match the schema in shared/schema.json) -------------
def _mock_extract_resume_text(filepath: str) -> str:
    logger.warning("Using MOCK extract_resume_text() for %s", filepath)
    return (
        "Jane Doe — Software Engineer. 3 years experience in Python, SQL, "
        "and REST API development. Built and deployed ML pipelines. "
        "B.Tech Computer Science."
    )


def _mock_analyze_resume(resume_text: str, jd_text: str) -> dict:
    if _fixture_cycle is not None:
        logger.warning("Using CAPTURED fixture for analyze_resume() (DEMO_MODE)")
        return next(_fixture_cycle)

    logger.warning("Using generic MOCK analyze_resume() — run capture_demo_fixtures.py first")
    return {
        "match_score": 78,
        "matched_skills": ["Python", "SQL", "REST APIs"],
        "missing_skills": ["Docker", "Kubernetes"],
        "candidate_feedback": [
            "Quantify your impact in the ML project bullet — add a metric.",
            "Move your Python/SQL skills higher, they match the JD's top requirement.",
        ],
        "recruiter_summary": "Strong technical fit, missing containerization experience.",
    }


extract_resume_text = _mock_extract_resume_text
analyze_resume = _mock_analyze_resume

if not DEMO_MODE:
    # --- try Ankitha's real module ---
    try:
        sys.path.insert(0, str(PARSING_DIR))
        from extract import extract_resume_text as _real_extract  # type: ignore

        extract_resume_text = _real_extract
        extraction_live = True
        logger.info("Loaded real extract_resume_text() from parsing/extract.py")
    except Exception as e:
        logger.warning("parsing/extract.py not available yet (%s) — using mock", e)

    # --- try Cherry's real module ---
    try:
        sys.path.insert(0, str(ANALYSIS_DIR))
        import analyze as _analyze_module  # type: ignore

        analyze_resume = _analyze_module.analyze_resume
        analysis_live = True
        # Cherry's module can optionally declare PROVIDER = "gemini" for
        # demo/judging transparency; falls back gracefully if she hasn't.
        analysis_provider = getattr(_analyze_module, "PROVIDER", "unknown")
        logger.info(
            "Loaded real analyze_resume() from analysis/analyze.py (provider=%s)",
            analysis_provider,
        )
    except ModuleNotFoundError as e:
        logger.warning(
            "analysis/analyze.py import failed on a missing package (%s). "
            "It runs on Gemini (google-genai) now, not Claude — did you "
            "install analysis/requirements.txt in THIS venv too? Falling back to mock.",
            e,
        )
    except Exception as e:
        logger.warning("analysis/analyze.py not available yet (%s) — using mock", e)