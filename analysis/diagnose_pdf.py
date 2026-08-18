"""
Diagnostic: figure out WHY extraction is coming back empty.
Tries pdfplumber (what batch_test.py uses) AND PyMuPDF (a different,
often more robust extractor) on the same files, and reports page counts,
text length, and whether pages contain embedded images (a sign of a
scanned/rasterized resume with no real text layer).

Run: python diagnose_pdf.py
Needs: pip install pymupdf
"""

import glob
import os

import pdfplumber
import fitz  # PyMuPDF

SAMPLE_DIR = "sample_resumes"


def diagnose(path: str):
    name = os.path.basename(path)
    print(f"\n=== {name} ===")

    # --- pdfplumber attempt ---
    try:
        with pdfplumber.open(path) as pdf:
            pages = len(pdf.pages)
            text_len = sum(len(p.extract_text() or "") for p in pdf.pages)
        print(f"  pdfplumber: {pages} page(s), {text_len} chars extracted")
    except Exception as e:
        print(f"  pdfplumber: FAILED — {e}")

    # --- PyMuPDF attempt ---
    try:
        doc = fitz.open(path)
        pages = len(doc)
        text_len = sum(len(page.get_text()) for page in doc)
        image_count = sum(len(page.get_images()) for page in doc)
        print(f"  PyMuPDF:    {pages} page(s), {text_len} chars extracted, "
              f"{image_count} embedded image(s)")
        doc.close()
    except Exception as e:
        print(f"  PyMuPDF: FAILED — {e}")


if __name__ == "__main__":
    pdf_paths = glob.glob(os.path.join(SAMPLE_DIR, "**", "*.pdf"), recursive=True)[:5]
    if not pdf_paths:
        print(f"No PDFs found in {SAMPLE_DIR}/")
    else:
        for p in pdf_paths:
            diagnose(p)
