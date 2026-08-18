import logging
import tempfile
import time
from pathlib import Path

from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    MIN_JD_LENGTH,
    ALLOWED_ORIGINS,
    LOG_LEVEL,
    DEMO_MODE,
)

from schemas import AnalysisResult, HealthStatus
import integrations


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("careersync.backend")


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="CareerSync API",
    version="1.0.0",
    description="Backend API for CareerSync resume analysis",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "CareerSync backend is running"
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health", response_model=HealthStatus)
async def health():

    return HealthStatus(
        status="ok",
        demo_mode=DEMO_MODE,
        extraction_live=integrations.extraction_live,
        analysis_live=integrations.analysis_live,
        analysis_provider=integrations.analysis_provider,
    )


# ---------------------------------------------------------
# MAIN ANALYZE ENDPOINT
# ---------------------------------------------------------

@app.post("/analyze", response_model=AnalysisResult)
async def analyze(
    resume: UploadFile,
    job_description: str = Form(...)
):

    request_start = time.monotonic()

    # -----------------------------------------------------
    # 1. VALIDATE FILE EXTENSION
    # -----------------------------------------------------

    filename = resume.filename or ""

    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Allowed: {sorted(ALLOWED_EXTENSIONS)}"
            ),
        )

    # -----------------------------------------------------
    # 2. VALIDATE JOB DESCRIPTION
    # -----------------------------------------------------

    jd_text = (job_description or "").strip()

    if len(jd_text) < MIN_JD_LENGTH:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Job description too short "
                f"(minimum {MIN_JD_LENGTH} characters)."
            ),
        )

    # -----------------------------------------------------
    # 3. READ UPLOADED FILE
    # -----------------------------------------------------

    contents = await resume.read()

    # Empty file
    if len(contents) == 0:

        raise HTTPException(
            status_code=422,
            detail="Uploaded resume file is empty.",
        )

    # File size
    if len(contents) > MAX_FILE_SIZE_BYTES:

        raise HTTPException(
            status_code=422,
            detail=(
                f"Resume file exceeds "
                f"{MAX_FILE_SIZE_MB}MB limit."
            ),
        )

    # -----------------------------------------------------
    # 4. CREATE UNIQUE TEMPORARY FILE
    # -----------------------------------------------------

    with tempfile.NamedTemporaryFile(
        suffix=ext,
        delete=False
    ) as tmp:

        tmp.write(contents)

        temp_path = tmp.name

    logger.info(
        "Received resume: %s",
        filename
    )

    # -----------------------------------------------------
    # 5. PIPELINE
    # -----------------------------------------------------

    try:

        # =================================================
        # STAGE 1 — RESUME TEXT EXTRACTION
        # =================================================

        try:

            logger.info(
                "Starting resume extraction..."
            )

            resume_text = integrations.extract_resume_text(
                temp_path
            )

        except Exception:

            logger.exception(
                "Resume extraction failed"
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "Could not extract text from "
                    "the resume file."
                ),
            )

        # -------------------------------------------------
        # CHECK EXTRACTED TEXT
        # -------------------------------------------------

        if not resume_text or not resume_text.strip():

            raise HTTPException(
                status_code=422,
                detail=(
                    "No readable text found in the resume. "
                    "The PDF may be scanned/image-only."
                ),
            )

        logger.info(
            "Resume extraction successful. "
            "Characters extracted: %d",
            len(resume_text)
        )

        # =================================================
        # STAGE 2 — RESUME ANALYSIS
        # =================================================

        try:

            logger.info(
                "Starting resume analysis..."
            )

            raw_result = integrations.analyze_resume(
                resume_text,
                jd_text
            )

        except Exception:

            logger.exception(
                "Resume analysis failed"
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "Analysis engine failed. "
                    "Please retry."
                ),
            )

        # =================================================
        # STAGE 3 — VALIDATE ANALYSIS RESULT
        # =================================================

        try:

            result = AnalysisResult.model_validate(
                raw_result
            )

        except ValidationError:

            logger.exception(
                "Analysis result does not match "
                "shared schema"
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "Analysis engine returned "
                    "malformed data."
                ),
            )

        # =================================================
        # SUCCESS
        # =================================================

        elapsed = time.monotonic() - request_start

        logger.info(
            "Analysis completed for %s "
            "in %.2f seconds. Score=%d",
            filename,
            elapsed,
            result.match_score,
        )

        return result

    finally:

        # -------------------------------------------------
        # ALWAYS DELETE TEMPORARY FILE
        # -------------------------------------------------

        Path(temp_path).unlink(
            missing_ok=True
        )

        logger.info(
            "Temporary file cleaned up."
        )