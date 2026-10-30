"""Tests for reading page text from a PDF (the PDF is generated inside the test)."""
import pymupdf

from src.extract import extract_pdf


def make_pdf(path, page_texts):
    """Write a small PDF with one page per string; an empty string makes a blank page."""
    doc = pymupdf.open()
    for text in page_texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 100), text)
    doc.save(str(path))
    doc.close()


def test_page_text_and_numbers_are_extracted(tmp_path):
    """Each page with real text is returned with its file name and 1-based page number."""
    pdf = tmp_path / "lecture.pdf"
    make_pdf(pdf, ["First page has enough text to count.", "Second page also has enough text."])
    pages, total, empty = extract_pdf(pdf)
    assert total == 2 and empty == 0
    assert [(p["file"], p["page"]) for p in pages] == [("lecture.pdf", 1), ("lecture.pdf", 2)]
    assert "First page" in pages[0]["text"]
    assert "Second page" in pages[1]["text"]


def test_blank_and_title_only_pages_are_counted_as_empty(tmp_path):
    """A blank page and a page with only a short title are skipped and counted as empty."""
    pdf = tmp_path / "slides.pdf"
    make_pdf(pdf, ["Real content on the first page, long enough.", "", "Title", "Real content on the fourth page, long enough."])
    pages, total, empty = extract_pdf(pdf)
    assert total == 4 and empty == 2
    assert [p["page"] for p in pages] == [1, 4]


def test_page_numbers_stay_aligned_with_the_pdf_after_skipped_pages(tmp_path):
    """Skipping an empty page does not shift the numbers of the pages after it."""
    pdf = tmp_path / "gap.pdf"
    make_pdf(pdf, ["", "", "Only the third page has enough text in it."])
    pages, _, _ = extract_pdf(pdf)
    assert [p["page"] for p in pages] == [3]
