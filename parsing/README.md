# CareerSync — `parsing/` (Role B, Ankitha)

Turns an uploaded resume file into clean plain text (+ optional lightweight
structured fields), for Cherry's Claude call to consume. This is the second
box in the pipeline: **Input → Parsing (you) → Claude analysis → Backend → Frontend**.

## Files

| File | Purpose |
|---|---|
| `extract.py` | **The contract.** `extract_resume_text(filepath) -> str`. PDF (+OCR fallback) and DOCX. This is the only function Nandu imports. |
| `structure.py` | Optional bonus signal: regex-based skills/contact/section extraction. Not required by the schema — useful for your own debugging and demo color. |
| `test_on_dataset.py` | Batch-runs `extract_resume_text` over a folder of real resumes and prints a pass/fail/timing summary. |
| `requirements.txt` | Python deps. |
| `data/` | Where you put the downloaded Kaggle dataset (gitignored — don't commit hundreds of PDFs to the repo). |

## Quick smoke test (no dataset download needed)

`fixtures/` ships with three throwaway sample resumes so you can verify your
environment before the real dataset finishes downloading:

```bash
python extract.py fixtures/sample_text_resume.pdf      # normal text-layer PDF
python extract.py fixtures/sample_scanned_resume.pdf    # image-only PDF -> exercises OCR fallback
python extract.py fixtures/sample_resume.docx           # docx with a table (skills often live there)
```

## Setup

```bash
cd parsing
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

**OCR needs two system binaries, not just pip packages** — this is the
part people usually miss:

- **Windows:** install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and [poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/), then add both `tesseract.exe` and poppler's `bin/` folder to your PATH.
- **Mac:** `brew install tesseract poppler`
- **Linux:** `sudo apt install tesseract-ocr poppler-utils`

If these aren't installed, `extract.py` still works fine for normal
text-based PDFs and DOCX files — it just logs a warning and returns empty
text for scanned PDFs instead of OCR'ing them. Nothing crashes.

## Why OCR fallback matters for *this specific dataset*

The Kaggle dataset linked for this project — [Resume Dataset PDF (hadikp)](https://www.kaggle.com/datasets/hadikp/resume-data-pdf) — is described by its author as a **"structured collection of categorized resume PDFs converted from images."**

That phrase is the whole ballgame for your role: a chunk of these PDFs have
**no real text layer at all** — they're just a picture of a resume wrapped
in a PDF container. `pdfplumber.extract_text()` will return `""` or
near-nothing for those. If you only wire up the "happy path" from the
handoff doc, a large fraction of your test set will silently fail and
you won't find out until demo day.

`extract.py` handles this: if the text layer comes back under ~40
characters, it automatically re-renders the PDF pages as images
(`pdf2image`) and runs Tesseract OCR on them, then uses whichever result is
longer. This was verified against a synthetic image-only PDF during
development — text layer returned 0 chars, OCR fallback recovered 125 chars
of real content automatically.

## Download the dataset

```bash
pip install kaggle
# requires ~/.kaggle/kaggle.json — get it from kaggle.com/settings > API > Create New Token
kaggle datasets download -d hadikp/resume-data-pdf -p data --unzip
```

If the unzipped structure isn't `data/<Category>/*.pdf`, point
`test_on_dataset.py` at wherever the PDFs actually landed:

```bash
python test_on_dataset.py path/to/actual/folder
```

## Day 1 workflow

1. `pip install -r requirements.txt`, confirm Tesseract + poppler are on PATH (`tesseract --version`, `pdftoppm -h`).
2. Download the dataset (above), or ask teammates for 2-3 of their own resumes to start with immediately if the Kaggle download is slow.
3. Run `python extract.py path/to/one_resume.pdf` — sanity check on a single file first.
4. Run `python test_on_dataset.py data` — batch-check across the whole dataset. Read the summary:
   - **Empty %** should trend toward 0 as you tune things. Any file that's still empty after OCR is a real edge case (corrupted file, unsupported encoding) — worth a look but not a blocker.
   - **Avg time/file** matters because Nandu's `/analyze` endpoint calls this synchronously per upload — if OCR is taking 3-4s/page that's fine for one demo upload, but don't run it over the whole dataset inside the live demo.
5. Push `extract.py` early (even a rough version) so Nandu can start integration — he's stubbing your function until it's real, but the real one unblocks the end-to-end pipeline test at the hour-16 checkpoint.

## Day 2 workflow

1. Look specifically at the files `test_on_dataset.py` flagged as `EMPTY` or `SHORT` — these are your "messy real-world resume" edge cases (the Day 2 goal in the handoff).
2. For genuinely unrecoverable files (corrupted, password-protected, unsupported format), confirm `extract_resume_text` degrades to `""` rather than raising — Nandu's endpoint should handle an empty string as "couldn't read this file" rather than a 500 error. Coordinate with him on what he wants back in that case (empty string vs. a specific sentinel — his call since he owns the endpoint contract).
3. If you have RAM/time budget left, `structure.py`'s skill list is intentionally short — extend `SKILL_KEYWORDS` with terms relevant to the JD categories you're actually testing against (the dataset's categories, e.g. IT, Design, Healthcare, etc., per the folder names) so your local sanity checks look sharper in the demo, even though Claude does the real matching.

## What you hand off

```python
from extract import extract_resume_text

text = extract_resume_text("uploaded_resume.pdf")   # -> str, never raises on "hard" files
```

Nandu calls this immediately after file upload in `backend/main.py`, then
passes `text` into Cherry's `analyze_resume(resume_text, jd_text)`. You do
not need to talk to the Claude API at all — that's Role A's job.
