"""Tests for dropping sources the agent cited but never saw."""
from src.helpers import validate_sources


def test_unseen_source_is_removed_and_counted():
    """A cited page that was never retrieved is dropped and counted."""
    result = {"answer": "x", "confidence": "high",
              "sources": [{"file": "a.pdf", "page": 9}]}
    out = validate_sources(result, seen={("a.pdf", 1)})
    assert out["sources"] == []
    assert out["unverified_sources_removed"] == 1


def test_seen_source_is_kept():
    """A cited page that was retrieved stays and nothing is counted as removed."""
    result = {"answer": "x", "confidence": "high",
              "sources": [{"file": "a.pdf", "page": 1}]}
    out = validate_sources(result, seen={("a.pdf", 1)})
    assert out["sources"] == [{"file": "a.pdf", "page": 1}]
    assert out["unverified_sources_removed"] == 0


def test_mixed_sources_keep_only_the_seen_ones():
    """With one seen and one unseen source, only the seen one survives."""
    result = {"answer": "x", "confidence": "medium",
              "sources": [{"file": "a.pdf", "page": 1}, {"file": "a.pdf", "page": 2}]}
    out = validate_sources(result, seen={("a.pdf", 2)})
    assert out["sources"] == [{"file": "a.pdf", "page": 2}]
    assert out["unverified_sources_removed"] == 1


def test_same_page_number_in_another_file_does_not_count_as_seen():
    """Seen pages are matched on file name and page number together."""
    result = {"answer": "x", "confidence": "high",
              "sources": [{"file": "b.pdf", "page": 1}]}
    out = validate_sources(result, seen={("a.pdf", 1)})
    assert out["sources"] == []


def test_not_found_answer_with_no_sources_is_unchanged():
    """A 'not_found' answer with an empty source list passes through untouched."""
    result = {"answer": "not in the notes", "confidence": "not_found", "sources": []}
    out = validate_sources(result, seen=set())
    assert out["sources"] == []
    assert out["confidence"] == "not_found"
    assert out["unverified_sources_removed"] == 0


def test_missing_sources_key_does_not_crash():
    """If the model omitted `sources`, the result gets an empty list."""
    out = validate_sources({"answer": "x", "confidence": "low"}, seen=set())
    assert out["sources"] == []


def test_input_dictionary_is_not_modified():
    """The function returns a new dict and leaves the original untouched."""
    result = {"answer": "x", "confidence": "high",
              "sources": [{"file": "a.pdf", "page": 9}]}
    validate_sources(result, seen=set())
    assert result["sources"] == [{"file": "a.pdf", "page": 9}]
    assert "unverified_sources_removed" not in result
