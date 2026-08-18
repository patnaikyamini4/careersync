"""
Random-samples PDFs from across the WHOLE dataset tree (not just the first
5 alphabetically) and reports what fraction actually have a text layer.
This tells us whether the empty-extraction problem is universal (whole
dataset is scanned images -> needs OCR) or isolated to certain folders
(e.g. "X" vs "X resumes" subfolders might differ).

Run: python sample_check.py
"""

import glob
import os
import random

import fitz  # PyMuPDF

SAMPLE_DIR = "sample_resumes"
SAMPLE_SIZE = 40


def has_text(path: str) -> int:
    """Returns char count of extracted text via PyMuPDF."""
    try:
        doc = fitz.open(path)
        text_len = sum(len(page.get_text()) for page in doc)
        doc.close()
        return text_len
    except Exception:
        return -1  # couldn't even open it


if __name__ == "__main__":
    all_pdfs = glob.glob(os.path.join(SAMPLE_DIR, "**", "*.pdf"), recursive=True)
    print(f"Total PDFs found: {len(all_pdfs)}")

    random.seed(42)
    sample = random.sample(all_pdfs, min(SAMPLE_SIZE, len(all_pdfs)))

    by_folder = {}
    with_text = 0
    without_text = 0
    broken = 0

    for path in sample:
        folder = os.path.basename(os.path.dirname(path))
        text_len = has_text(path)
        by_folder.setdefault(folder, {"text": 0, "no_text": 0})

        if text_len > 50:
            with_text += 1
            by_folder[folder]["text"] += 1
        elif text_len == -1:
            broken += 1
        else:
            without_text += 1
            by_folder[folder]["no_text"] += 1

    print(f"\nSampled {len(sample)} PDFs from across the dataset:")
    print(f"  Has real text (>50 chars):  {with_text}")
    print(f"  No text (scanned/image):    {without_text}")
    print(f"  Failed to open:             {broken}")

    print(f"\nBreakdown by folder:")
    for folder, counts in sorted(by_folder.items()):
        print(f"  {folder}: {counts['text']} with text, {counts['no_text']} without")
