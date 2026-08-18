"""
Day-1/Day-2 goal: run analyze_resume() against a batch of REAL resumes from
the Kaggle dataset, not just hand-written samples. This is how you catch
prompt failures (invalid JSON, hallucinated skills, generic feedback) before
Ankitha's real parser is even plugged in.

Uses pdfplumber directly here (not Ankitha's module) so Role A can test
independently and in parallel, per the handoff doc — you don't wait on B.

Run: python batch_test.py
"""

import os
import json
import glob
import pdfplumber

from analyze import analyze_resume

SAMPLE_DIR = "sample_resumes"
JD = """
We're hiring a Backend Engineer. Must have: Python, REST API design,
SQL/PostgreSQL, Docker, Kubernetes experience, cloud (AWS/GCP/Azure).
Nice to have: Go, CI/CD, microservices experience.
"""


def extract_text(pdf_path: str) -> str:
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)


def run_batch(limit: int = 10):
    pdf_paths = glob.glob(os.path.join(SAMPLE_DIR, "**", "*.pdf"), recursive=True)[:limit]
    if not pdf_paths:
        print(f"No PDFs found in {SAMPLE_DIR}/ — run download_sample_data.py first.")
        return

    results = []
    successes = 0

    for path in pdf_paths:
        name = os.path.basename(path)
        print(f"\n--- {name} ---")
        try:
            resume_text = extract_text(path)
            if not resume_text.strip():
                print("  (empty extraction — likely a scanned/image PDF, skipping)")
                continue

            result = analyze_resume(resume_text, JD)
            successes += 1
            print(f"  match_score={result['match_score']}  "
                  f"matched={len(result['matched_skills'])}  "
                  f"missing={len(result['missing_skills'])}")
            results.append({"file": name, "result": result})
        except Exception as e:
            print(f"  FAILED: {e}")
            results.append({"file": name, "error": str(e)})

    print(f"\n=== {successes}/{len(pdf_paths)} succeeded ===")

    with open("batch_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Full results written to batch_test_results.json")


if __name__ == "__main__":
    run_batch(limit=10)
