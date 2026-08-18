"""
Generates 8 realistic, varied resumes as plain .txt files for testing the
prompt — used INSTEAD of the Kaggle dataset, since that dataset turned out
to be 100% scanned images with no text layer (confirmed via sample_check.py:
0/40 sampled PDFs had any extractable text).

This gives real variety (strong match, weak match, career changer, senior
vs junior, buzzword-heavy but shallow, concise-but-strong) without fighting
OCR infrastructure that isn't Role A's job to solve.

Run once: python generate_test_resumes.py
Then:     python text_batch_test.py
"""

import os

OUT_DIR = "sample_resumes_text"

RESUMES = {
    "strong_backend.txt": """
Meera Nair — Backend Engineer
5 years building and scaling REST APIs in Python (Django, FastAPI).
Designed and optimized PostgreSQL schemas handling 10M+ rows.
Containerized all services with Docker; ran production workloads on a
Kubernetes cluster (EKS) with autoscaling and rolling deployments.
Built CI/CD pipelines with GitHub Actions, cut deploy time from 40min to 6min.
Comfortable with AWS (EC2, RDS, S3, IAM).
""",
    "weak_frontend.txt": """
Arjun Mehta — Frontend Developer
2 years building UIs in React and Vue. Strong with Tailwind CSS,
Figma-to-code workflows, and accessibility audits. Built a component
library used across 4 internal products. No backend or infrastructure
experience; have used REST APIs as a consumer, never built one.
""",
    "career_changer.txt": """
Sana Iqbal — Career Changer, ex-Mechanical Engineer
8 years in mechanical design (SolidWorks, AutoCAD), no professional
software experience. Completed a 6-month backend bootcamp: built 2
portfolio projects with Python/Flask and SQLite, deployed one to Render.
No experience with Docker, Kubernetes, or production-scale systems.
Strong fundamentals, eager to learn, currently studying for AWS
Cloud Practitioner cert.
""",
    "senior_overqualified.txt": """
Dr. Ravi Krishnan — Principal Engineer / Distributed Systems
14 years. Led backend architecture for a fintech platform processing
2M transactions/day: Python and Go services, PostgreSQL with read
replicas, Kubernetes on GCP with custom operators, full observability
stack (Prometheus/Grafana). Published 3 internal RFCs on service mesh
migration. Managed a team of 6 engineers.
""",
    "buzzword_shallow.txt": """
Deepak Rao — Software Professional
Passionate and driven full-stack ninja rockstar with expertise in
synergizing cutting-edge solutions. Proficient in "modern technologies"
and "best practices." Team player, fast learner, detail-oriented.
Worked on various projects using various tools to deliver various results.
""",
    "concise_strong.txt": """
Fatima Sheikh — Backend Engineer, 3 YOE
Python/FastAPI, PostgreSQL, Docker, Kubernetes (GKE), Terraform for IaC.
Built the order-processing service at a logistics startup (Go-live: 99.95%
uptime over 18 months). REST API design, OpenAPI specs, contract testing.
""",
    "thin_new_grad.txt": """
Karan Joshi
Recent CS graduate. Did some Python projects in college. Looking for
opportunities. Familiar with basic programming concepts.
""",
    "mismatched_domain.txt": """
Neha Kapoor — Registered Nurse, 6 years
ICU and emergency care experience across two hospitals. Certified in
ACLS and PALS. Managed patient care coordination and electronic health
record systems (Epic). No software development or programming background.
""",
}

JD = """
We're hiring a Backend Engineer. Must have: Python, REST API design,
SQL/PostgreSQL, Docker, Kubernetes experience, cloud (AWS/GCP/Azure).
Nice to have: Go, CI/CD, microservices experience.
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for filename, content in RESUMES.items():
        with open(os.path.join(OUT_DIR, filename), "w", encoding="utf-8") as f:
            f.write(content.strip())
    with open(os.path.join(OUT_DIR, "_jd.txt"), "w", encoding="utf-8") as f:
        f.write(JD.strip())
    print(f"Wrote {len(RESUMES)} test resumes + JD to {OUT_DIR}/")


if __name__ == "__main__":
    main()
