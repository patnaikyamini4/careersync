"""
test_on_dataset.py — Role B (Ankitha): batch-test extract_resume_text()
against a folder of real resumes.

This is your Day-1/Day-2 robustness harness. The handoff doc's #1 rule for
your role is: "Test against 5+ real resumes early — this is the #1 place
hackathon demos break." This script automates that.

Dataset assumed: Kaggle "Resume Dataset PDF" (hadikp/resume-data-pdf) —
"categorized resume PDFs converted from images". Download it with the
Kaggle CLI:

    pip install kaggle
    kaggle datasets download -d hadikp/resume-data-pdf -p data --unzip

Expected layout after unzip (category-per-folder is the common Kaggle shape
for this kind of dataset — adjust DATA_DIR below if yours differs):

    data/
      <Category1>/*.pdf
      <Category2>/*.pdf
      ...

Because this dataset is explicitly described as PDFs "converted from
images", expect a meaningful fraction to have NO text layer — that's
exactly the OCR fallback path in extract.py being exercised. Watch the
ocr_used count in the summary; if it's 0 across a scanned dataset, your
OCR fallback threshold or dependencies need a look.

Usage:
    python test_on_dataset.py [data_dir]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from extract import extract_resume_text, MIN_TEXT_LENGTH_BEFORE_OCR_FALLBACK
from structure import parse_resume_structured

DEFAULT_DATA_DIR = "data"
SUPPORTED_EXTS = (".pdf", ".docx")


def find_resume_files(data_dir: Path) -> list[Path]:
    return [p for p in data_dir.rglob("*") if p.suffix.lower() in SUPPORTED_EXTS]


def run(data_dir: Path):
    files = find_resume_files(data_dir)
    if not files:
        print(f"No .pdf/.docx files found under {data_dir}. "
              f"Download the dataset first (see docstring) or pass a different path.")
        return

    print(f"Found {len(files)} resume files under {data_dir}\n")

    results = []
    t0 = time.time()

    for i, path in enumerate(files, 1):
        file_t0 = time.time()
        status = "ok"
        text = ""
        error = None
        try:
            text = extract_resume_text(str(path))
        except Exception as e:
            status = "error"
            error = str(e)

        elapsed = time.time() - file_t0
        char_count = len(text)
        empty = char_count == 0
        likely_scanned = char_count < MIN_TEXT_LENGTH_BEFORE_OCR_FALLBACK

        results.append({
            "path": str(path),
            "category": path.parent.name,
            "status": status,
            "chars": char_count,
            "empty": empty,
            "seconds": round(elapsed, 2),
            "error": error,
        })

        flag = "EMPTY" if empty else ("SHORT" if likely_scanned else "ok")
        print(f"[{i}/{len(files)}] {path.name[:50]:<50} "
              f"chars={char_count:<6} {flag:<6} ({elapsed:.2f}s)"
              + (f"  ERROR: {error}" if error else ""))

    total_elapsed = time.time() - t0

    # --- summary -----------------------------------------------------
    n = len(results)
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_empty = sum(1 for r in results if r["empty"])
    n_error = sum(1 for r in results if r["status"] == "error")
    avg_chars = sum(r["chars"] for r in results) / n if n else 0
    avg_time = sum(r["seconds"] for r in results) / n if n else 0

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files:            {n}")
    print(f"Extracted successfully: {n_ok} ({n_ok / n:.0%})")
    print(f"Empty text (failures):  {n_empty} ({n_empty / n:.0%})")
    print(f"Raised errors:          {n_error}")
    print(f"Avg chars extracted:    {avg_chars:.0f}")
    print(f"Avg time / file:        {avg_time:.2f}s")
    print(f"Total wall time:        {total_elapsed:.1f}s")

    if n_empty > 0:
        print(f"\n{n_empty} file(s) returned empty text — likely scanned "
              f"PDFs where OCR also failed. Check that poppler-utils and "
              f"tesseract-ocr are installed (see README) and re-run.")
        for r in results:
            if r["empty"]:
                print(f"  - {r['path']}")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_DATA_DIR)
    run(target)

