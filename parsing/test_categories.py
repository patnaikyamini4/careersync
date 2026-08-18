from pathlib import Path
from extract import extract_resume_text
from structure import parse_resume_structured

DATA_DIR = Path("data/Resumes PDF")

# Categories to test
categories = [
    "Accountant",
    "Advocate",
    "Arts",
    "Business Development",
    "Civil Engineer",
    "Data Science",
    "Designer",
    "HR",
    "Information Technology",
    "Teacher",
]

print("=" * 70)
print("CATEGORY TEST")
print("=" * 70)

for category in categories:
    folder = DATA_DIR / category

    if not folder.exists():
        print(f"\n❌ {category}: folder not found")
        continue

    pdfs = list(folder.glob("*.pdf"))

    if not pdfs:
        print(f"\n❌ {category}: no PDF files found")
        continue

    pdf = pdfs[0]

    print(f"\n📄 Category: {category}")
    print(f"File: {pdf.name}")

    try:
        text = extract_resume_text(str(pdf))
        result = parse_resume_structured(text)

        print(f"Characters extracted: {len(text)}")
        print(f"Email: {result['contact']['email']}")
        print(f"Phone: {result['contact']['phone']}")
        print(f"LinkedIn: {result['contact']['linkedin']}")
        print(f"Skills detected: {result['skills']}")
        print(f"Sections detected: {list(result['sections'].keys())}")

        print("STATUS: ✅ OK")

    except Exception as e:
        print(f"STATUS: ❌ ERROR")
        print(f"Error: {e}")

print("\n" + "=" * 70)
print("CATEGORY TEST COMPLETE")
print("=" * 70)