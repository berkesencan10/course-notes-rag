"""Read every PDF in data/notes page by page and save the text to data/pages.json."""
import json
from pathlib import Path
import pymupdf

MIN_CHARS = 30  # pages with less text than this are treated as empty / image-only


def extract_pdf(pdf_path, min_chars=MIN_CHARS):
    """Return (pages, total_pages, empty_pages) for one PDF."""
    pdf_path = Path(pdf_path)
    doc = pymupdf.open(pdf_path)
    pages, empty = [], 0
    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if len(text) < min_chars:
            empty += 1
            continue
        pages.append({"file": pdf_path.name, "page": i, "text": text})
    total = len(doc)
    doc.close()
    return pages, total, empty


def main():
    pages = []
    for pdf_path in sorted(Path("data/notes").glob("*.pdf")):
        found, total, empty = extract_pdf(pdf_path)
        pages.extend(found)
        print(f"{pdf_path.name}: {total} pages, {empty} empty/image-only pages")

    Path("data").mkdir(exist_ok=True)
    with open("data/pages.json", "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False)
    print(f"\nTotal: {len(pages)} pages saved")


if __name__ == "__main__":
    main()
