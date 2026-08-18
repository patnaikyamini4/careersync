"""
Central configuration for the CareerSync backend.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

PARSING_DIR = BASE_DIR / "parsing"

ANALYSIS_DIR = BASE_DIR / "analysis"


# ---------------------------------------------------------
# FILE SETTINGS
# ---------------------------------------------------------

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
}

MAX_FILE_SIZE_MB = int(
    os.getenv(
        "MAX_FILE_SIZE_MB",
        "10"
    )
)

MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)


# ---------------------------------------------------------
# JOB DESCRIPTION SETTINGS
# ---------------------------------------------------------

MIN_JD_LENGTH = int(
    os.getenv(
        "MIN_JD_LENGTH",
        "20"
    )
)


# ---------------------------------------------------------
# DEMO MODE
# ---------------------------------------------------------

DEMO_MODE = (
    os.getenv(
        "DEMO_MODE",
        "false"
    ).lower()
    == "true"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501"
).split(",")


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)