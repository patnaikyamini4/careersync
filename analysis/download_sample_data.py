"""
One-time setup: pulls the Kaggle "resume-data-pdf" dataset locally so you
have real, messy resumes to test the prompt against — instead of only your
own hand-written samples.

Dataset: https://www.kaggle.com/datasets/hadikp/resume-data-pdf

Setup (once):
  1. pip install kaggle
  2. Go to kaggle.com -> Account -> "Create New API Token", download kaggle.json
  3. Place it at ~/.kaggle/kaggle.json  (Windows: C:\\Users\\<you>\\.kaggle\\kaggle.json)
  4. Run: python download_sample_data.py

This drops raw resume PDFs into ./sample_resumes/
"""

import os
import zipfile
import subprocess

DATASET = "hadikp/resume-data-pdf"
OUT_DIR = "sample_resumes"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Downloading {DATASET} via kaggle CLI ...")
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET, "-p", OUT_DIR],
        check=True,
    )

    # unzip whatever came down
    for fname in os.listdir(OUT_DIR):
        if fname.endswith(".zip"):
            zpath = os.path.join(OUT_DIR, fname)
            print(f"Unzipping {zpath} ...")
            with zipfile.ZipFile(zpath, "r") as z:
                z.extractall(OUT_DIR)
            os.remove(zpath)

    print(f"Done. Resumes are in ./{OUT_DIR}/")


if __name__ == "__main__":
    main()
