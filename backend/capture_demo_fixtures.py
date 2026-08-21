"""
Captures REAL backend responses into backend/fixtures/*.json so DEMO_MODE
can replay genuine, previously-validated results instead of one repeated
generic mock. Safer for judging — if someone runs the demo twice, they see
two different real outputs instead of the same canned number both times.

Run this ONCE while the pipeline is genuinely live (extraction_live=true,
analysis_live=true, DEMO_MODE=false) — right now, since you just confirmed
that in Swagger. Feed it 2-4 resumes spanning different match qualities
(strong / partial / weak, like the SAP BI/BW example you just got) so the
replayed demo shows a realistic spread, not four near-identical scores.

Usage (pairs of resume + JD, at least one pair):
    python capture_demo_fixtures.py resume1.pdf "jd text" resume2.pdf jd2.txt ...
"""
import json
import sys
from pathlib import Path

import requests

from config import FIXTURES_DIR

BASE_URL = "http://localhost:8000"


def capture(resume_path: str, jd_arg: str, index: int) -> bool:
    path = Path(resume_path)
    if not path.exists():
        print(f"SKIP: file not found — {path}")
        return False

    jd_text = Path(jd_arg).read_text(encoding="utf-8") if Path(jd_arg).exists() else jd_arg

    with open(path, "rb") as f:
        files = {"resume": (path.name, f)}
        data = {"job_description": jd_text}
        resp = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=90)

    if resp.status_code != 200:
        print(f"SKIP {path.name}: got {resp.status_code} — {resp.text}")
        return False

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIXTURES_DIR / f"fixture_{index}.json"
    body = resp.json()
    out_path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    print(f"Captured {path.name} -> {out_path.name} (score={body['match_score']})")
    return True


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2 != 0:
        print(__doc__)
        sys.exit(1)

    health = requests.get(f"{BASE_URL}/health", timeout=5).json()
    if health.get("demo_mode") or not (health.get("extraction_live") and health.get("analysis_live")):
        print("Backend isn't running LIVE right now (need DEMO_MODE=false, both")
        print("extraction_live and analysis_live true). Current health:")
        print(health)
        sys.exit(1)

    count = 0
    for i in range(0, len(args), 2):
        if capture(args[i], args[i + 1], count):
            count += 1

    print(f"\n{count} fixtures captured to {FIXTURES_DIR}/")
    print("Set DEMO_MODE=true in .env to replay these instead of live calls.")
