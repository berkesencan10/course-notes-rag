"""Tests for splitting page text into chunks."""
from src.helpers import split_text


def test_long_text_is_split_at_1500_characters():
    """A 3200-character text becomes chunks of 1500, 1500 and 200 characters."""
    chunks = split_text("a" * 3200)
    assert [len(c) for c in chunks] == [1500, 1500, 200]


def test_chunks_join_back_to_the_original_text():
    """No text is lost or duplicated when splitting."""
    text = "".join(str(i % 10) for i in range(4321))
    assert "".join(split_text(text)) == text


def test_short_text_stays_in_one_chunk():
    """Text shorter than the limit is returned as a single chunk."""
    assert split_text("short slide text") == ["short slide text"]


def test_text_of_exactly_1500_characters_is_one_chunk():
    """The boundary case: exactly 1500 characters does not create an empty second chunk."""
    assert len(split_text("b" * 1500)) == 1


def test_empty_text_does_not_crash_and_gives_no_chunks():
    """An empty string returns an empty list instead of raising."""
    assert split_text("") == []
