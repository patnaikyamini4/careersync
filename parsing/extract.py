"""
extract.py — Role B (Ankitha): Resume file -> clean plain text.

Public contract:
    extract_resume_text(filepath: str) -> str

CareerSync OCR pipeline:

    PDF
      |
      +--> pdfplumber text extraction
      |
      +--> enough text?
             |
             +--> YES -> clean text -> return
             |
             +--> NO
                    |
                    v
                 pdf2image
                    |
                    v
                  Poppler
                    |
                    v
                 PDF pages
                    |
                    v
                Tesseract OCR
                    |
                    v
                 clean text
                    |
                    v
                Resume text

Design goals:
- Lightweight enough for an 8 GB RAM machine.
- No heavy local ML models.
- Normal text PDFs use the fast pdfplumber path.
- Image/scanned PDFs automatically fall back to OCR.
- Tesseract and Poppler paths are explicitly configured for Windows.
- Individual page failures do not crash the whole extraction.
- Bad/corrupt files degrade gracefully where possible.
- PDF encoding artifacts such as (cid:127) are removed.
- Unicode and whitespace are normalized.
- DOCX paragraphs and tables are supported.
- Public API remains:
      extract_resume_text(filepath: str) -> str
"""

from __future__ import annotations

import logging
import os
import re
import sys
import unicodedata
from pathlib import Path


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger("careersync.parsing")

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# ============================================================================
# WINDOWS OCR CONFIGURATION
# ============================================================================

# Your actual installation paths.
#
# Environment variables can override these defaults:
#
# CAREERSYNC_TESSERACT_PATH
# CAREERSYNC_POPPLER_PATH

DEFAULT_TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

DEFAULT_POPPLER_PATH = (
    r"C:\Program Files\poppler"
    r"\poppler-26.02.0"
    r"\Library"
    r"\bin"
)


def configure_ocr_paths() -> None:
    """
    Configure Tesseract and Poppler paths.

    Environment variables can override the defaults:

        CAREERSYNC_TESSERACT_PATH
        CAREERSYNC_POPPLER_PATH

    This makes the code portable if the project is moved to another machine.
    """

    global TESSERACT_PATH
    global POPPLER_PATH

    TESSERACT_PATH = os.environ.get(
        "CAREERSYNC_TESSERACT_PATH",
        DEFAULT_TESSERACT_PATH,
    )

    POPPLER_PATH = os.environ.get(
        "CAREERSYNC_POPPLER_PATH",
        DEFAULT_POPPLER_PATH,
    )

    logger.info(
        "Configured Tesseract path: %s",
        TESSERACT_PATH,
    )

    logger.info(
        "Configured Poppler path: %s",
        POPPLER_PATH,
    )


configure_ocr_paths()


# ============================================================================
# EXTRACTION SETTINGS
# ============================================================================

# If pdfplumber extracts fewer than this many non-whitespace characters,
# we assume the PDF may be scanned/image-only and try OCR.

MIN_TEXT_LENGTH_BEFORE_OCR_FALLBACK = 40

# OCR rendering resolution.
#
# 200 DPI:
# - good OCR quality
# - lower memory than 300 DPI
# - appropriate for an 8 GB RAM machine

OCR_DPI = 200

# Tesseract OCR language.

OCR_LANGUAGE = "eng"

# Tesseract page segmentation mode.
#
# 3 = Fully automatic page segmentation.
# Good default for resumes with multiple blocks/columns.

TESSERACT_CONFIG = "--psm 3"

# Maximum number of characters to display in CLI preview.

CLI_OUTPUT_PREVIEW_LENGTH = 1500


# ============================================================================
# CUSTOM ERROR
# ============================================================================

class ExtractionError(Exception):
    """
    Raised only for genuinely unsupported input or missing files.

    Normal PDF/DOCX extraction problems are intentionally handled gracefully.
    """


# ============================================================================
# OPTIONAL DEPENDENCY HELPERS
# ============================================================================

def _check_tesseract_available() -> bool:
    """
    Check whether the configured Tesseract executable exists.
    """

    if not os.path.isfile(TESSERACT_PATH):
        logger.warning(
            "Tesseract executable not found at: %s",
            TESSERACT_PATH,
        )
        return False

    return True


def _check_poppler_available() -> bool:
    """
    Check whether the configured Poppler directory exists and contains
    pdftoppm.exe on Windows.
    """

    pdftoppm_path = os.path.join(
        POPPLER_PATH,
        "pdftoppm.exe",
    )

    if not os.path.isfile(pdftoppm_path):
        logger.warning(
            "Poppler pdftoppm.exe not found at: %s",
            pdftoppm_path,
        )
        return False

    return True


# ============================================================================
# TEXT CLEANING
# ============================================================================

def clean_extracted_text(text: str) -> str:
    """
    Clean text extracted from PDF/DOCX files before sending it
    to the analysis engine.

    Handles:

    - PDF CID/glyph artifacts such as:
          (cid:127)
          (CID:128)

    - bracketed CID artifacts such as:
          [cid:127]

    - Unicode normalization

    - invisible/control characters

    - non-breaking spaces

    - Unicode dash normalization

    - curly quote normalization

    - excessive spaces

    - excessive blank lines

    - trailing/leading whitespace

    The function intentionally does NOT try to guess missing characters.
    If a PDF contains an unresolved glyph, it is replaced with a space
    rather than inventing content.
    """

    if not text:
        return ""

    # ------------------------------------------------------------------------
    # 1. Normalize Unicode
    # ------------------------------------------------------------------------

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    # ------------------------------------------------------------------------
    # 2. Remove unresolved PDF CID/glyph artifacts
    #
    # Examples:
    #
    #     (cid:127)
    #     (CID:127)
    #     ( cid : 127 )
    #     [cid:127]
    #     [ CID : 127 ]
    #
    # These artifacts are common when a PDF's font encoding cannot be
    # correctly interpreted by the PDF text extractor.
    # ------------------------------------------------------------------------

    text = re.sub(
        r"[\(\[]\s*cid\s*:\s*\d+\s*[\)\]]",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # ------------------------------------------------------------------------
    # 3. Remove any remaining control/invisible characters.
    #
    # Preserve:
    #     \n = newline
    #     \t = tab
    #
    # This removes characters from Unicode control categories.
    # ------------------------------------------------------------------------

    text = "".join(
        char
        for char in text
        if (
            char in "\n\t"
            or not unicodedata.category(char).startswith("C")
        )
    )

    # ------------------------------------------------------------------------
    # 4. Normalize non-breaking spaces.
    # ------------------------------------------------------------------------

    text = text.replace(
        "\u00a0",
        " ",
    )

    # ------------------------------------------------------------------------
    # 5. Normalize common Unicode dash characters.
    # ------------------------------------------------------------------------

    text = text.replace("\u2010", "-")  # Hyphen
    text = text.replace("\u2011", "-")  # Non-breaking hyphen
    text = text.replace("\u2012", "-")  # Figure dash
    text = text.replace("\u2013", "-")  # En dash
    text = text.replace("\u2014", "-")  # Em dash
    text = text.replace("\u2212", "-")  # Minus sign

    # ------------------------------------------------------------------------
    # 6. Normalize curly quotes.
    # ------------------------------------------------------------------------

    text = text.replace("\u2018", "'")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201c", '"')
    text = text.replace("\u201d", '"')

    # ------------------------------------------------------------------------
    # 7. Normalize common bullet characters.
    #
    # Preserve them as a simple ASCII bullet representation.
    # ------------------------------------------------------------------------

    text = text.replace("\u2022", "-")
    text = text.replace("\u2023", "-")
    text = text.replace("\u25E6", "-")
    text = text.replace("\u2043", "-")

    # ------------------------------------------------------------------------
    # 8. Remove trailing whitespace from every line.
    # ------------------------------------------------------------------------

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    # ------------------------------------------------------------------------
    # 9. Rebuild text.
    # ------------------------------------------------------------------------

    text = "\n".join(lines)

    # ------------------------------------------------------------------------
    # 10. Collapse excessive spaces/tabs.
    #
    # Example:
    #
    #     Python        Developer
    #
    # becomes:
    #
    #     Python Developer
    # ------------------------------------------------------------------------

    text = re.sub(
        r"[ \t]{2,}",
        " ",
        text,
    )

    # ------------------------------------------------------------------------
    # 11. Collapse excessive blank lines.
    # ------------------------------------------------------------------------

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    # ------------------------------------------------------------------------
    # 12. Remove spaces immediately before line breaks.
    # ------------------------------------------------------------------------

    text = re.sub(
        r"[ \t]+\n",
        "\n",
        text,
    )

    # ------------------------------------------------------------------------
    # 13. Remove spaces immediately after line breaks.
    # ------------------------------------------------------------------------

    text = re.sub(
        r"\n[ \t]+",
        "\n",
        text,
    )

    # ------------------------------------------------------------------------
    # 14. Final cleanup.
    # ------------------------------------------------------------------------

    return text.strip()


# ============================================================================
# PDF TEXT-LAYER EXTRACTION
# ============================================================================

def _extract_pdf_text_layer(filepath: str) -> str:
    """
    Extract text directly from a PDF using pdfplumber.

    This is the fast path and should be used for normal text-based PDFs.
    """

    try:
        import pdfplumber

    except ImportError:

        logger.error(
            "pdfplumber is not installed. "
            "Install it with: pip install pdfplumber"
        )

        return ""

    parts: list[str] = []

    try:

        with pdfplumber.open(filepath) as pdf:

            logger.info(
                "PDF opened successfully: %s | pages=%d",
                filepath,
                len(pdf.pages),
            )

            for page_number, page in enumerate(
                pdf.pages,
                start=1,
            ):

                try:

                    page_text = page.extract_text()

                    if page_text and page_text.strip():

                        parts.append(page_text)

                except Exception as exc:

                    logger.warning(
                        "Text extraction failed on page %d of %s: %s",
                        page_number,
                        filepath,
                        exc,
                    )

    except Exception as exc:

        logger.warning(
            "pdfplumber failed on %s: %s",
            filepath,
            exc,
        )

        return ""

    return "\n".join(parts).strip()


# ============================================================================
# OCR FALLBACK
# ============================================================================

def _extract_pdf_via_ocr(filepath: str) -> str:
    """
    OCR fallback for scanned/image-only PDFs.

    Uses:

        PDF -> Poppler -> image -> Tesseract -> text

    Pages are processed one at a time to reduce RAM usage.
    """

    # ------------------------------------------------------------------------
    # Import OCR dependencies lazily.
    # ------------------------------------------------------------------------

    try:

        from pdf2image import convert_from_path

    except ImportError:

        logger.warning(
            "pdf2image is not installed. "
            "Install with: pip install pdf2image"
        )

        return ""

    try:

        import pytesseract

    except ImportError:

        logger.warning(
            "pytesseract is not installed. "
            "Install with: pip install pytesseract"
        )

        return ""

    # ------------------------------------------------------------------------
    # Verify Tesseract.
    # ------------------------------------------------------------------------

    if not _check_tesseract_available():

        logger.error(
            "OCR cannot run because Tesseract was not found."
        )

        return ""

    # ------------------------------------------------------------------------
    # Verify Poppler.
    # ------------------------------------------------------------------------

    if not _check_poppler_available():

        logger.error(
            "OCR cannot run because Poppler/pdftoppm was not found."
        )

        return ""

    # ------------------------------------------------------------------------
    # Explicitly configure Tesseract.
    # ------------------------------------------------------------------------

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

    logger.info(
        "Starting OCR for scanned PDF: %s",
        filepath,
    )

    logger.info(
        "Tesseract: %s",
        TESSERACT_PATH,
    )

    logger.info(
        "Poppler: %s",
        POPPLER_PATH,
    )

    # ------------------------------------------------------------------------
    # Determine page count first.
    # ------------------------------------------------------------------------

    try:

        import pdfplumber

        with pdfplumber.open(filepath) as pdf:

            total_pages = len(pdf.pages)

    except Exception as exc:

        logger.warning(
            "Could not determine PDF page count for OCR: %s",
            exc,
        )

        total_pages = None

    if total_pages is not None:

        logger.info(
            "OCR will process %d page(s) at %d DPI",
            total_pages,
            OCR_DPI,
        )

    # ------------------------------------------------------------------------
    # If page count cannot be determined, do not attempt OCR blindly.
    # ------------------------------------------------------------------------

    if total_pages is None:

        return ""

    # ------------------------------------------------------------------------
    # OCR page by page.
    #
    # IMPORTANT:
    # We intentionally process one page at a time.
    #
    # This is better for an 8 GB RAM machine than loading all pages
    # into memory at once.
    # ------------------------------------------------------------------------

    parts: list[str] = []

    for page_number in range(
        1,
        total_pages + 1,
    ):

        image = None

        try:

            logger.info(
                "OCR processing page %d/%d",
                page_number,
                total_pages,
            )

            # --------------------------------------------------------------
            # Render only one page.
            # --------------------------------------------------------------

            images = convert_from_path(
                filepath,
                dpi=OCR_DPI,
                first_page=page_number,
                last_page=page_number,
                poppler_path=POPPLER_PATH,
                fmt="png",
                thread_count=1,
            )

            if not images:

                logger.warning(
                    "Poppler returned no image for page %d",
                    page_number,
                )

                continue

            image = images[0]

            # --------------------------------------------------------------
            # OCR the page.
            # --------------------------------------------------------------

            page_text = pytesseract.image_to_string(
                image,
                lang=OCR_LANGUAGE,
                config=TESSERACT_CONFIG,
            )

            if page_text and page_text.strip():

                cleaned_page_text = clean_extracted_text(
                    page_text
                )

                if cleaned_page_text:

                    parts.append(
                        cleaned_page_text
                    )

                logger.info(
                    "Page %d OCR extracted %d characters",
                    page_number,
                    len(cleaned_page_text),
                )

            else:

                logger.warning(
                    "Page %d OCR produced no text",
                    page_number,
                )

        except Exception as exc:

            logger.warning(
                "OCR failed on page %d of %s: %s",
                page_number,
                filepath,
                exc,
            )

        finally:

            # --------------------------------------------------------------
            # Explicitly release the image.
            #
            # This matters when processing many resumes on an 8 GB machine.
            # --------------------------------------------------------------

            try:

                if image is not None:
                    image.close()

            except Exception:
                pass

            image = None

    # ------------------------------------------------------------------------
    # Combine OCR pages.
    # ------------------------------------------------------------------------

    final_text = "\n\n".join(
        parts
    ).strip()

    # ------------------------------------------------------------------------
    # Final cleaning.
    # ------------------------------------------------------------------------

    final_text = clean_extracted_text(
        final_text
    )

    logger.info(
        "OCR completed: %s | extracted=%d characters",
        filepath,
        len(final_text),
    )

    return final_text


# ============================================================================
# PDF EXTRACTION
# ============================================================================

def extract_text_pdf(
    filepath: str,
    allow_ocr_fallback: bool = True,
) -> str:
    """
    Extract text from a PDF.

    Strategy:

        1. Try pdfplumber text layer.
        2. Clean extracted text.
        3. If text is too short, use OCR.
        4. Clean OCR result.
        5. Return whichever result contains more useful text.
    """

    logger.info(
        "Extracting PDF: %s",
        filepath,
    )

    # ------------------------------------------------------------------------
    # First attempt: normal PDF text layer.
    # ------------------------------------------------------------------------

    raw_text = _extract_pdf_text_layer(
        filepath
    )

    raw_text_length = len(
        raw_text.strip()
    )

    logger.info(
        "pdfplumber extracted %d characters from %s",
        raw_text_length,
        filepath,
    )

    # ------------------------------------------------------------------------
    # IMPORTANT:
    # Clean the pdfplumber output BEFORE deciding whether it is sufficient.
    # ------------------------------------------------------------------------

    text = clean_extracted_text(
        raw_text
    )

    text_length = len(
        text.strip()
    )

    logger.info(
        "Cleaned PDF text: %d -> %d characters",
        raw_text_length,
        text_length,
    )

    # ------------------------------------------------------------------------
    # If enough clean text was found, no OCR is needed.
    # ------------------------------------------------------------------------

    if text_length >= MIN_TEXT_LENGTH_BEFORE_OCR_FALLBACK:

        logger.info(
            "PDF contains sufficient text layer. OCR not required."
        )

        return text

    # ------------------------------------------------------------------------
    # OCR fallback disabled.
    # ------------------------------------------------------------------------

    if not allow_ocr_fallback:

        logger.info(
            "OCR fallback disabled. Returning cleaned PDF text layer."
        )

        return text

    # ------------------------------------------------------------------------
    # OCR fallback.
    # ------------------------------------------------------------------------

    logger.info(
        "PDF text layer looks empty/scanned (%d chars). "
        "Starting OCR fallback.",
        text_length,
    )

    ocr_text = _extract_pdf_via_ocr(
        filepath
    )

    ocr_text = clean_extracted_text(
        ocr_text
    )

    ocr_length = len(
        ocr_text.strip()
    )

    logger.info(
        "OCR extracted %d characters from %s",
        ocr_length,
        filepath,
    )

    # ------------------------------------------------------------------------
    # Return whichever result is better.
    # ------------------------------------------------------------------------

    if ocr_length > text_length:

        logger.info(
            "Using OCR result because it contains more text."
        )

        return ocr_text

    logger.info(
        "Using pdfplumber result because it contains equal/more text."
    )

    return text


# ============================================================================
# DOCX EXTRACTION
# ============================================================================

def extract_text_docx(filepath: str) -> str:
    """
    Extract text from a DOCX.

    Includes:

    - normal paragraphs
    - tables

    Tables are important because many resume templates put
    contact information, skills, education, or experience inside tables.
    """

    try:

        from docx import Document

    except ImportError:

        logger.warning(
            "python-docx is not installed. "
            "Install with: pip install python-docx"
        )

        return ""

    logger.info(
        "Extracting DOCX: %s",
        filepath,
    )

    try:

        doc = Document(
            filepath
        )

    except Exception as exc:

        logger.warning(
            "python-docx failed to open %s: %s",
            filepath,
            exc,
        )

        return ""

    parts: list[str] = []

    # ------------------------------------------------------------------------
    # Paragraphs.
    # ------------------------------------------------------------------------

    for paragraph in doc.paragraphs:

        text = paragraph.text.strip()

        if text:

            parts.append(
                text
            )

    # ------------------------------------------------------------------------
    # Tables.
    #
    # Resume templates often put contact information and skills inside
    # tables. We therefore extract table cell text too.
    # ------------------------------------------------------------------------

    for table in doc.tables:

        for row in table.rows:

            row_parts: list[str] = []

            for cell in row.cells:

                cell_text = cell.text.strip()

                if cell_text:

                    row_parts.append(
                        cell_text
                    )

            if row_parts:

                parts.append(
                    " | ".join(row_parts)
                )

    # ------------------------------------------------------------------------
    # Combine.
    # ------------------------------------------------------------------------

    final_text = "\n".join(
        parts
    ).strip()

    # ------------------------------------------------------------------------
    # Apply the SAME cleaning pipeline used by PDF extraction.
    # ------------------------------------------------------------------------

    final_text = clean_extracted_text(
        final_text
    )

    logger.info(
        "DOCX extraction completed: %d characters",
        len(final_text),
    )

    return final_text


# ============================================================================
# PUBLIC ENTRY POINT
# ============================================================================

def extract_resume_text(filepath: str) -> str:
    """
    Public CareerSync extraction function.

    Parameters
    ----------
    filepath:
        Path to a .pdf or .docx resume.

    Returns
    -------
    str
        Cleaned extracted plain text.

    Raises
    ------
    ExtractionError
        Only when:
        - file does not exist
        - path is not a file
        - unsupported file extension

    Normal extraction/OCR failures do NOT raise an exception.
    They return whatever text could be extracted.
    """

    # ------------------------------------------------------------------------
    # Validate path.
    # ------------------------------------------------------------------------

    if not filepath:

        raise ExtractionError(
            "No resume filepath was provided."
        )

    path = Path(
        filepath
    )

    if not path.exists():

        raise ExtractionError(
            f"File not found: {filepath}"
        )

    if not path.is_file():

        raise ExtractionError(
            f"Path is not a file: {filepath}"
        )

    # ------------------------------------------------------------------------
    # Normalize extension.
    # ------------------------------------------------------------------------

    lower = path.suffix.lower()

    # ------------------------------------------------------------------------
    # PDF.
    # ------------------------------------------------------------------------

    if lower == ".pdf":

        text = extract_text_pdf(
            str(path),
            allow_ocr_fallback=True,
        )

    # ------------------------------------------------------------------------
    # DOCX.
    # ------------------------------------------------------------------------

    elif lower == ".docx":

        text = extract_text_docx(
            str(path)
        )

    # ------------------------------------------------------------------------
    # Unsupported.
    # ------------------------------------------------------------------------

    else:

        raise ExtractionError(
            f"Unsupported file type: {filepath}. "
            f"Only .pdf and .docx are supported."
        )

    # ------------------------------------------------------------------------
    # FINAL CLEANUP
    #
    # This is intentionally performed AGAIN at the public boundary.
    #
    # That guarantees that no matter which extraction path was used:
    #
    # PDF text layer
    # OCR
    # DOCX
    #
    # the backend always receives cleaned text.
    # ------------------------------------------------------------------------

    text = clean_extracted_text(
        text
    )

    # ------------------------------------------------------------------------
    # Empty result.
    # ------------------------------------------------------------------------

    if not text:

        logger.warning(
            "Extraction produced EMPTY text for: %s",
            filepath,
        )

    else:

        logger.info(
            "Final extraction result: %d characters | %s",
            len(text),
            filepath,
        )

    return text


# ============================================================================
# OCR SYSTEM TEST
# ============================================================================

def test_ocr_setup() -> bool:
    """
    Test Tesseract and Poppler configuration.

    Returns:
        True if both are available.
        False otherwise.
    """

    print("\n" + "=" * 70)
    print("CareerSync OCR SYSTEM TEST")
    print("=" * 70)

    # ------------------------------------------------------------------------
    # Tesseract.
    # ------------------------------------------------------------------------

    print("\n[1/2] Checking Tesseract...")

    if not _check_tesseract_available():

        print("❌ Tesseract NOT FOUND")
        print(
            f"Expected: {TESSERACT_PATH}"
        )

        return False

    try:

        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = (
            TESSERACT_PATH
        )

        version = pytesseract.get_tesseract_version()

        print("✅ Tesseract OK")
        print(
            f"   Path: {TESSERACT_PATH}"
        )
        print(
            f"   Version: {version}"
        )

    except Exception as exc:

        print(
            "❌ Tesseract Python test FAILED"
        )
        print(
            f"   Error: {exc}"
        )

        return False

    # ------------------------------------------------------------------------
    # Poppler.
    # ------------------------------------------------------------------------

    print("\n[2/2] Checking Poppler...")

    if not _check_poppler_available():

        print("❌ Poppler NOT FOUND")
        print(
            f"Expected: {POPPLER_PATH}"
        )

        return False

    print("✅ Poppler OK")
    print(
        f"   Path: {POPPLER_PATH}"
    )

    print(
        "   pdftoppm: "
        f"{os.path.join(POPPLER_PATH, 'pdftoppm.exe')}"
    )

    print("\n" + "=" * 70)
    print("✅ OCR SYSTEM READY")
    print("=" * 70)

    return True


# ============================================================================
# COMMAND-LINE INTERFACE
# ============================================================================

def main() -> None:
    """
    Command-line usage:

        python extract.py <resume.pdf>

    or:

        python extract.py <resume.docx>

    or:

        python extract.py --test
    """

    # ------------------------------------------------------------------------
    # OCR system test.
    # ------------------------------------------------------------------------

    if (
        len(sys.argv) == 2
        and sys.argv[1] == "--test"
    ):

        success = test_ocr_setup()

        sys.exit(
            0 if success else 1
        )

    # ------------------------------------------------------------------------
    # Normal extraction.
    # ------------------------------------------------------------------------

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "  python extract.py <resume.pdf|resume.docx>\n"
            "  python extract.py --test"
        )

        sys.exit(1)

    filepath = sys.argv[1]

    try:

        result = extract_resume_text(
            filepath
        )

    except ExtractionError as exc:

        print(
            f"\n❌ Extraction error: {exc}"
        )

        sys.exit(1)

    except Exception as exc:

        # Defensive protection for a demo environment.

        logger.exception(
            "Unexpected extraction error: %s",
            exc,
        )

        print(
            f"\n❌ Unexpected extraction error: {exc}"
        )

        sys.exit(1)

    # ------------------------------------------------------------------------
    # Display result.
    # ------------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("CAREERSYNC RESUME EXTRACTION")
    print("=" * 70)

    print(
        f"\nFile: {filepath}"
    )

    print(
        f"Characters extracted: {len(result)}"
    )

    print(
        "\n--- EXTRACTED TEXT PREVIEW ---\n"
    )

    if result:

        print(
            result[
                :CLI_OUTPUT_PREVIEW_LENGTH
            ]
        )

        if (
            len(result)
            > CLI_OUTPUT_PREVIEW_LENGTH
        ):

            print(
                "\n...[preview truncated]..."
            )

    else:

        print(
            "⚠️ No text was extracted."
        )

    print(
        "\n" + "=" * 70
    )


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()