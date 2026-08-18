from pathlib import Path
import shutil

SOURCE = Path("data/Resumes PDF")
DEST = Path("data/test_sample")

MAX_FILES = 100

DEST.mkdir(parents=True, exist_ok=True)

count = 0

for pdf in SOURCE.rglob("*.pdf"):
    # Keep the original category folder
    relative = pdf.relative_to(SOURCE)
    destination = DEST / relative

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pdf, destination)

    count += 1

    if count >= MAX_FILES:
        break

print(f"Copied {count} PDF files to {DEST}")