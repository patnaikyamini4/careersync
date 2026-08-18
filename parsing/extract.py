"""
extract.py — Role B (Ankitha): resume file -> clean plain text.

Public contract (this is what Nandu/Role D imports into the backend):

    extract_resume_text(filepath: str) -> str

Design goals for this file, given the constraints on ANKITHA18 (8GB RAM):
  - No heavy local ML models. pdfplumber + python-docx only for the happy path.
  - The CareerSync dataset (Kaggle "Resume Dataset PDF") is explicitly
    "categorized resume PDFs converted from images" -> a meaningful chunk of
    it will be scanned/rasterized PDFs with NO extractable text layer.
    pdfplumber returns "" or near-empty text for those. We detect that and
    fall back to OCR (pdf2image + pytesseract) instead of crashing or
    silently returning nothing.
  - Never raise on a "normal" bad file during a demo. Log the problem and
    degrade to whatever text we could get (even partial/empty), because a
    pipeline that returns *something* beats one that throws a 500 during
    the judges' demo.
"""

from __future__ import annotations

import logging
import os

import pdfplumber
from docx import Document

logger = logging.getLogger("careersync.parsing")
logging.basicConfig(level=logging.INFO)

# Below this many characters, we treat pdfplumber's output as "not real text"
# and assume the PDF is a scanned image -> trigger OCR fallback.
MIN_TEXT_LENGTH_BEFORE_OCR_FALLBACK = 40


class ExtractionError(Exception):
    """Raised only for truly unsupported input (e.g. wrong file type).
    Never raised for 'this PDF was hard to read' — that degrades instead."""


# --------------------------------------------------------------------------
# PDF extraction
# --------------------------------------------------------------------------

def extract_text_pdf(filepath: str, allow_ocr_fallback: bool = True) -> str:
    """Extract text from a PDF. Tries the fast text layer first (pdfplumber);
    if that yields (almost) nothing, falls back to OCR — this is what makes
    scanned/Canva-exported resumes survive instead of returning ''.
    """
    text = _extract_pdf_text_layer(filepath)

    if len(text.strip()) < MIN_TEXT_LENGTH_BEFORE_OCR_FALLBACK and allow_ocr_fallback:
        logger.info("PDF text layer looks empty/scanned (%s) — trying OCR: %s",
                    len(text.strip()), filepath)
        ocr_text = _extract_pdf_via_ocr(filepath)
        if len(ocr_text.strip()) > len(text.strip()):
            text = ocr_text

    return text.strip()


def _extract_pdf_text_layer(filepath: str) -> str:
    parts = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    parts.append(page_text)
    except Exception as e:
        # Corrupt / password-protected / malformed PDF — don't crash the pipeline.
        logger.warning("pdfplumber failed on %s: %s", filepath, e)
    return "\n".join(parts)


def _extract_pdf_via_ocr(filepath: str) -> str:
    """OCR fallback for image-only PDFs. Requires system packages
    'poppler-utils' (for pdf2image) and 'tesseract-ocr' to be installed —
    see README for install commands. Kept lazy-imported so the happy path
    (text-based PDFs) never pays this cost or needs these dependencies.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        logger.warning(
            "OCR fallback requested but pdf2image/pytesseract not installed. "
            "Run: pip install pdf2image pytesseract  (and install poppler + tesseract)"
        )
        return ""

    try:
        # 200 dpi is a good speed/accuracy tradeoff on 8GB RAM machines.
        images = convert_from_path(filepath, dpi=200)
    except Exception as e:
        logger.warning("OCR page rasterization failed on %s: %s", filepath, e)
        return ""

    parts = []
    for i, image in enumerate(images):
        try:
            parts.append(pytesseract.image_to_string(image))
        except Exception as e:
            logger.warning("OCR failed on page %d of %s: %s", i, filepath, e)
    return "\n".join(parts)


# --------------------------------------------------------------------------
# DOCX extraction
# --------------------------------------------------------------------------

def extract_text_docx(filepath: str) -> str:
    """Extract text from a .docx, including text inside tables — a lot of
    resume templates put the skills/contact block in a table, which a naive
    paragraph-only reader silently drops."""
    try:
        doc = Document(filepath)
    except Exception as e:
        logger.warning("python-docx failed to open %s: %s", filepath, e)
        return ""

    parts = [p.text for p in doc.paragraphs if p.text.strip()]

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)

    return "\n".join(parts).strip()


# --------------------------------------------------------------------------
# Public entrypoint — this is the function Nandu (Role D) imports
# --------------------------------------------------------------------------

def extract_resume_text(filepath: str) -> str:
    """filepath -> clean plain text. Raises ExtractionError only for a
    genuinely unsupported extension; every other failure mode degrades to
    a best-effort (possibly empty) string instead of raising, per the
    Day 2 goal: 'don't crash, degrade to plain text if structured
    extraction fails.'
    """
    if not os.path.exists(filepath):
        raise ExtractionError(f"File not found: {filepath}")

    lower = filepath.lower()
    if lower.endswith(".pdf"):
        text = extract_text_pdf(filepath)
    elif lower.endswith(".docx"):
        text = extract_text_docx(filepath)
    else:
        raise ExtractionError(
            f"Unsupported file type: {filepath} (only .pdf and .docx are supported)"
        )

    if not text.strip():
        logger.warning("Extraction produced empty text for %s — check if it's a "
                        "scanned PDF with OCR disabled, or a corrupted file.", filepath)

    return text


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python extract.py <path_to_resume.pdf|.docx>")
        sys.exit(1)

    result = extract_resume_text(sys.argv[1])
    print(f"--- Extracted {len(result)} characters ---")
    print(result[:1000])
