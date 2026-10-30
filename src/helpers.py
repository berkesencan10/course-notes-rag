"""Pure helper functions (no PDF, Chroma or API access) so they can be unit tested."""
import re

CHUNK_SIZE = 1500
SIMILARITY_THRESHOLD = 0.7


def split_text(text, size=CHUNK_SIZE):
    """Split text into consecutive chunks of at most `size` characters."""
    return [text[i:i + size] for i in range(0, len(text), size)]


def words(text):
    """Lower-cased set of word tokens, used to compare pages."""
    return set(re.findall(r"\w+", text.lower()))


def dedupe_pages(candidates, limit):
    """Keep ranked (file, page, text) candidates, skipping near-duplicates of earlier ones.

    Returns up to `limit` (file, page) pairs in the original rank order.
    """
    picked, picked_words = [], []
    for file, page, text in candidates:
        w = words(text)
        if any(len(w & o) / max(len(w | o), 1) > SIMILARITY_THRESHOLD for o in picked_words):
            continue
        picked.append((file, page))
        picked_words.append(w)
        if len(picked) == limit:
            break
    return picked


def expand_neighbours(picked, available, n):
    """Add up to `n` pages on each side of every picked (file, page).

    Only pages present in `available` are kept, so the first and last pages never overflow.
    Returns a sorted list without duplicates.
    """
    wanted = set()
    for file, page in picked:
        for k in range(-n, n + 1):
            key = (file, page + k)
            if key in available:
                wanted.add(key)
    return sorted(wanted)


def validate_sources(result, seen):
    """Drop cited (file, page) sources that were never seen; report how many were removed."""
    out = dict(result)
    sources = out.get("sources", [])
    kept = [s for s in sources if (s["file"], s["page"]) in seen]
    out["unverified_sources_removed"] = len(sources) - len(kept)
    out["sources"] = kept
    return out
