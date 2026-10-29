"""Read every PDF in data/notes page by page and save the text to data/pages.json."""
import json
from pathlib import Path
import pymupdf

pages = []
for pdf_path in sorted(Path("data/notes").glob("*.pdf")):
    doc = pymupdf.open(pdf_path)
    empty = 0
    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if len(text) < 30:
            empty += 1
            continue
        pages.append({"file": pdf_path.name, "page": i, "text": text})
    print(f"{pdf_path.name}: {len(doc)} pages, {empty} empty/image-only pages")

Path("data").mkdir(exist_ok=True)
with open("data/pages.json", "w", encoding="utf-8") as f:
    json.dump(pages, f, ensure_ascii=False)
print(f"\nTotal: {len(pages)} pages saved")
