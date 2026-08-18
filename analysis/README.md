# Role A (Chandu/Cherry) — LLM / Prompt Engineer — Detailed Workflow

Your slice of the pipeline: **parsed resume text + JD text → validated JSON**
(the box after "Parsing and extraction", before "Backend orchestration API"
in the diagram). Everything below is scoped to `analysis/`, matches the
`shared/schema.json` contract, and exposes exactly one function Nandu
imports: `analyze_resume(resume_text, jd_text) -> dict`.

## Files in this folder

| File | Purpose |
|---|---|
| `schema.py` | Pydantic model mirroring `shared/schema.json`. Every Claude response gets validated against this before it leaves your code. |
| `analyze.py` | The real thing — system prompt, Claude call, JSON extraction, retry-with-repair, validation. `analyze_resume()` lives here. |
| `test_call.py` | Day-1 smoke test: 3 hand-written cases (strong match, partial match, thin/edge-case resume). |
| `download_sample_data.py` | Pulls the Kaggle `hadikp/resume-data-pdf` dataset so you test against real, messy resumes instead of only your own samples. |
| `batch_test.py` | Runs the prompt against a batch of real Kaggle PDFs, reports a pass rate, dumps results to `batch_test_results.json`. |
| `requirements.txt` | Everything you need installed. |

## Step-by-step

### 1. Environment (5 min)
```bash
cd analysis
python -m venv venv
venv\Scripts\activate          # Windows; use `source venv/bin/activate` on mac/linux
pip install -r requirements.txt
```
Create `analysis/.env` (this is in `.gitignore` already, per the shared setup):
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
```

### 2. Smoke test with hand-written samples (Day 1, first hour)
```bash
python test_call.py
```
This proves the core loop works before you touch real data: Claude call →
strip markdown fences → `json.loads` → Pydantic validation → retry-with-repair
if either step fails. If this passes for all 3 cases (including the thin
"John. Looking for a job." edge case), your foundation is solid.

### 3. Get real test data from Kaggle (Day 1, next ~20 min)
The hand-written cases above are too clean — real resumes have weird PDF
extraction artifacts, inconsistent formatting, and Canva-template layouts
that pdfplumber mangles. Use the actual dataset to stress-test the prompt:

```bash
pip install kaggle
# get an API token from kaggle.com -> Account -> Create New API Token
# save it to ~/.kaggle/kaggle.json (chmod 600 on mac/linux)
python download_sample_data.py
```
This downloads [`hadikp/resume-data-pdf`](https://www.kaggle.com/datasets/hadikp/resume-data-pdf)
into `sample_resumes/`.

### 4. Batch test against real resumes
```bash
python batch_test.py
```
This extracts text with `pdfplumber` directly (you don't need to wait for
Ankitha's `extract_resume_text()` to exist — you're testing your prompt in
parallel, per the handoff doc), runs each through `analyze_resume()`, and
reports:
- how many returned valid schema-conformant JSON
- match scores per resume, so you can eyeball whether scoring feels sane
- full results in `batch_test_results.json` for closer review

**What to look for while reviewing results:**
- Are `matched_skills` actually skill names, not sentences or hallucinations?
- Does `candidate_feedback` reference something specific in that resume, or
  is it generic filler? (The system prompt explicitly forbids generic advice
  — if you see it anyway, tighten the prompt.)
- Any PDFs that returned empty text (scanned/image-based resumes)? Those
  are Ankitha's problem to flag, not yours to fix — but worth a heads-up to
  her early.
- Any JSON parse failures that survived both retries? If a pattern shows up
  (e.g. always fails on resumes with tables), adjust the system prompt.

### 5. Prompt refinement loop (Day 1 afternoon → Day 2)
Iterate directly on `SYSTEM_PROMPT` in `analyze.py`. Re-run `batch_test.py`
after each change — treat it as your regression suite. Priority order:
1. **Reliability first** — 100% valid JSON across the batch before anything else.
2. **No hallucinated skills** — `matched_skills`/`missing_skills` must be
   traceable to actual text in the resume/JD.
3. **Feedback quality** — specific and actionable, not generic.
4. **Edge cases** — thin resumes, zero-overlap resumes, resumes with no
   clear skills section.

### 6. Hand off to Nandu
Nandu imports your function directly:
```python
from analyze import analyze_resume
result = analyze_resume(resume_text, job_description)
```
He'll stub this with mock schema JSON until it's ready (per the handoff
doc), then swap in the real import — so ship early, even a rough version,
so he can wire the pipeline without waiting on your polish pass.

## Design decisions baked into `analyze.py`

- **Structured output via strict prompting**, not tool-use/JSON mode — kept
  simple for a 2-day hackathon; `_extract_json()` handles the common case of
  Claude wrapping output in markdown fences anyway.
- **Retry-with-repair**: on invalid JSON or a Pydantic validation error, the
  failure reason is fed back to Claude verbatim and it's asked to correct
  itself — this catches almost all transient formatting slips in 1 retry.
- **Validation is the real contract**, not just "is this valid JSON" —
  `schema.py` enforces types, score bounds (0-100), non-empty feedback, and
  dedupes skill lists, so B/C/D never see malformed data even if Claude's
  raw output is slightly off.
- **Edge cases handled in the prompt itself** (thin resumes, zero overlap)
  rather than in Python — keeps the function simple and puts the judgment
  call where the model is actually good at it: reading the resume.
