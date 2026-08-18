"""
Day-1 goal: prove analyze_resume() reliably returns valid JSON.
Run: python test_call.py
"""

import json
from analyze import analyze_resume

TEST_CASES = [
    {
        "name": "strong_match",
        "resume": """
        Rahul Verma — Software Engineer
        4 years building REST APIs in Python (Flask, FastAPI). Strong SQL,
        worked extensively with PostgreSQL. Containerized services with Docker
        and deployed to a Kubernetes cluster on GCP. Familiar with CI/CD (GitHub Actions).
        """,
        "jd": """
        Backend Engineer — must have Python, REST API design, SQL, Docker,
        Kubernetes. Nice to have: GCP, CI/CD experience.
        """,
    },
    {
        "name": "partial_match",
        "resume": """
        Ananya Iyer — Frontend Developer
        3 years React, TypeScript, Tailwind CSS. Built dashboards consuming
        REST APIs. No backend or infra experience.
        """,
        "jd": """
        Backend Engineer — must have Python, REST API design, SQL, Docker,
        Kubernetes.
        """,
    },
    {
        "name": "thin_resume_edge_case",
        "resume": "John. Looking for a job. Good with computers.",
        "jd": """
        Backend Engineer — must have Python, REST API design, SQL, Docker,
        Kubernetes.
        """,
    },
]

if __name__ == "__main__":
    for case in TEST_CASES:
        print(f"\n=== {case['name']} ===")
        try:
            result = analyze_resume(case["resume"], case["jd"])
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"FAILED: {e}")
