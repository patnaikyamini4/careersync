"""
Batch-tests analyze_resume() against the 8 varied text resumes from
generate_test_resumes.py. Replaces batch_test.py's role (that script's
Kaggle PDFs turned out to be 100% scanned images with no text layer).

Run: python generate_test_resumes.py   (once, to create the files)
     python text_batch_test.py
"""

import os
import glob
import json

from analyze import analyze_resume

SAMPLE_DIR = "sample_resumes_text"


def main():
    jd_path = os.path.join(SAMPLE_DIR, "_jd.txt")
    if not os.path.exists(jd_path):
        print(f"Run 'python generate_test_resumes.py' first.")
        return

    with open(jd_path, encoding="utf-8") as f:
        jd = f.read()

    resume_paths = sorted(
        p for p in glob.glob(os.path.join(SAMPLE_DIR, "*.txt"))
        if not p.endswith("_jd.txt")
    )

    results = []
    for path in resume_paths:
        name = os.path.basename(path)
        print(f"\n--- {name} ---")
        with open(path, encoding="utf-8") as f:
            resume_text = f.read()

        try:
            result = analyze_resume(resume_text, jd)
            print(f"  match_score={result['match_score']}")
            print(f"  matched: {result['matched_skills']}")
            print(f"  missing: {result['missing_skills']}")
            print(f"  summary: {result['recruiter_summary']}")
            results.append({"file": name, "result": result})
        except Exception as e:
            print(f"  FAILED: {e}")
            results.append({"file": name, "error": str(e)})

    with open("text_batch_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results written to text_batch_results.json")


if __name__ == "__main__":
    main()
