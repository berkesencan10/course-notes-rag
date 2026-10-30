"""Tests for adding neighbouring pages around the retrieved ones."""
from src.helpers import expand_neighbours

PAGES = {("a.pdf", p) for p in range(1, 11)}  # a.pdf has pages 1..10


def test_middle_page_gets_pages_on_both_sides():
    """Page 5 with 2 neighbours becomes pages 3 to 7."""
    assert expand_neighbours([("a.pdf", 5)], PAGES, 2) == [("a.pdf", p) for p in range(3, 8)]


def test_first_page_does_not_go_below_one():
    """Page 1 with 2 neighbours gives pages 1 to 3 and no page 0 or -1."""
    assert expand_neighbours([("a.pdf", 1)], PAGES, 2) == [("a.pdf", 1), ("a.pdf", 2), ("a.pdf", 3)]


def test_last_page_does_not_go_past_the_end():
    """Page 10 with 2 neighbours gives pages 8 to 10 and no page 11 or 12."""
    assert expand_neighbours([("a.pdf", 10)], PAGES, 2) == [("a.pdf", 8), ("a.pdf", 9), ("a.pdf", 10)]


def test_overlapping_neighbours_are_merged_without_duplicates():
    """Pages 3 and 4 with 1 neighbour give pages 2 to 5, each once."""
    out = expand_neighbours([("a.pdf", 3), ("a.pdf", 4)], PAGES, 1)
    assert out == [("a.pdf", p) for p in range(2, 6)]


def test_pages_missing_from_the_notes_are_skipped():
    """An image-only page that was not extracted is simply not included."""
    pages = PAGES - {("a.pdf", 6)}
    assert ("a.pdf", 6) not in expand_neighbours([("a.pdf", 5)], pages, 2)


def test_neighbours_stay_inside_their_own_file():
    """Pages of another file are never added as neighbours."""
    pages = PAGES | {("b.pdf", 5)}
    out = expand_neighbours([("a.pdf", 5)], pages, 1)
    assert all(file == "a.pdf" for file, _ in out)


def test_zero_neighbours_returns_only_the_picked_pages():
    """With n=0 only the retrieved pages come back."""
    assert expand_neighbours([("a.pdf", 5)], PAGES, 0) == [("a.pdf", 5)]
