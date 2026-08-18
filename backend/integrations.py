"""
Integration layer for CareerSync.

This module connects:

    Ankitha's parser
            ↓
    Nandu's backend
            ↓
    Cherry's analyzer

Until the real modules are available,
mock implementations are used automatically.
"""

import logging
import sys

from config import (
    PARSING_DIR,
    ANALYSIS_DIR,
    DEMO_MODE,
)


# ---------------------------------------------------------
# LOGGER
# ---------------------------------------------------------

logger = logging.getLogger(
    "careersync.integrations"
)


# ---------------------------------------------------------
# STATUS FLAGS
# ---------------------------------------------------------

extraction_live = False

analysis_live = False

analysis_provider = "mock"


# =========================================================
# MOCK RESUME EXTRACTION
# =========================================================

def _mock_extract_resume_text(
    filepath: str
) -> str:

    logger.warning(
        "Using MOCK resume extraction for %s",
        filepath
    )

    return (
        "Jane Doe\n"
        "Software Engineer\n\n"

        "Experience:\n"
        "3 years of experience in software development.\n"
        "Worked with Python, SQL and REST APIs.\n"
        "Built machine learning pipelines.\n\n"

        "Skills:\n"
        "Python, SQL, REST APIs, Git\n\n"

        "Education:\n"
        "B.Tech Computer Science"
    )


# =========================================================
# MOCK ANALYSIS
# =========================================================

def _mock_analyze_resume(
    resume_text: str,
    jd_text: str
) -> dict:

    logger.warning(
        "Using MOCK resume analysis"
    )

    return {

        "match_score": 78,

        "matched_skills": [
            "Python",
            "SQL",
            "REST APIs",
        ],

        "missing_skills": [
            "Docker",
            "Kubernetes",
        ],

        "candidate_feedback": [

            "Quantify your impact "
            "in the ML project bullet "
            "by adding a measurable metric.",

            "Move your Python and SQL "
            "skills higher because they "
            "match important JD requirements.",
        ],

        "recruiter_summary": (
            "Strong technical fit with "
            "some missing containerization "
            "experience."
        ),
    }


# ---------------------------------------------------------
# DEFAULT TO MOCK FUNCTIONS
# ---------------------------------------------------------

extract_resume_text = (
    _mock_extract_resume_text
)

analyze_resume = (
    _mock_analyze_resume
)


# =========================================================
# LOAD REAL PARSER
# =========================================================

if not DEMO_MODE:

    try:

        sys.path.insert(
            0,
            str(PARSING_DIR)
        )

        from extract import (
            extract_resume_text as real_extract_resume_text
        )

        extract_resume_text = (
            real_extract_resume_text
        )

        extraction_live = True

        logger.info(
            "Real resume parser loaded."
        )

    except Exception as e:

        logger.warning(
            "Real parser unavailable. "
            "Using mock parser. Error: %s",
            e
        )


# =========================================================
# LOAD REAL ANALYZER
# =========================================================

if not DEMO_MODE:

    try:

        sys.path.insert(
            0,
            str(ANALYSIS_DIR)
        )

        import analyze as analysis_module

        analyze_resume = (
            analysis_module.analyze_resume
        )

        analysis_live = True

        analysis_provider = getattr(
            analysis_module,
            "PROVIDER",
            "unknown"
        )

        logger.info(
            "Real analysis module loaded. "
            "Provider=%s",
            analysis_provider
        )

    except Exception as e:

        logger.warning(
            "Real analysis module unavailable. "
            "Using mock analyzer. Error: %s",
            e
        )