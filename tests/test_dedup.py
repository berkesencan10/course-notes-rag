"""Tests for removing near-duplicate pages (slide animation frames)."""
from src.helpers import dedupe_pages

FRAME = "Alpha-beta pruning A B 8 D 10 2 C E G 19 4"


def test_near_identical_frame_is_dropped():
    """A page that differs by one word from an earlier page is removed."""
    candidates = [("games.pdf", 47, FRAME), ("games.pdf", 48, FRAME + " 35")]
    assert dedupe_pages(candidates, limit=5) == [("games.pdf", 47)]


def test_different_pages_are_kept():
    """Pages about different topics are both kept."""
    candidates = [
        ("search.pdf", 52, "Breadth-first search uses a FIFO queue"),
        ("search.pdf", 71, "Depth-first search uses a LIFO stack"),
    ]
    assert dedupe_pages(candidates, limit=5) == [("search.pdf", 52), ("search.pdf", 71)]


def test_the_higher_ranked_duplicate_is_the_one_kept():
    """Of two near-identical pages the first (best ranked) survives, in rank order."""
    candidates = [
        ("games.pdf", 66, FRAME),
        ("search.pdf", 10, "Uniform cost search expands the cheapest node"),
        ("games.pdf", 47, FRAME),
    ]
    assert dedupe_pages(candidates, limit=5) == [("games.pdf", 66), ("search.pdf", 10)]


def test_limit_is_respected():
    """No more than `limit` pages are returned."""
    candidates = [("f.pdf", i, f"unique{i} topic{i} words{i}") for i in range(10)]
    assert dedupe_pages(candidates, limit=3) == [("f.pdf", 0), ("f.pdf", 1), ("f.pdf", 2)]


def test_similarity_exactly_at_the_threshold_is_not_a_duplicate():
    """Two pages with word overlap of exactly 0.7 are both kept (the check is strictly greater)."""
    common = "w1 w2 w3 w4 w5 w6 w7"
    candidates = [("f.pdf", 1, common + " x1 x2"), ("f.pdf", 2, common + " y1")]
    assert dedupe_pages(candidates, limit=5) == [("f.pdf", 1), ("f.pdf", 2)]


def test_no_candidates_gives_no_pages():
    """An empty search result does not crash."""
    assert dedupe_pages([], limit=5) == []
