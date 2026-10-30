"""Classic RAG: vector search, near-duplicate removal, neighbouring pages, one Claude call."""
import json
import os
import anthropic
import chromadb
from src.helpers import dedupe_pages, expand_neighbours

MODEL = "claude-sonnet-5-5"
NEIGHBORS = int(os.environ.get("RAG_NEIGHBORS", "2"))  # neighbouring pages added on each side
N_CANDIDATES = 30  # candidates fetched from the vector search
N_PICKED = 6       # pages kept after removing near-duplicates

_pages = json.load(open("data/pages.json", encoding="utf-8"))
_page_text = {(p["file"], p["page"]): p["text"] for p in _pages}
_col = chromadb.PersistentClient(path="chroma_db").get_collection("notes")
_client = anthropic.Anthropic()
USAGE = {"in": 0, "out": 0}


def _ranked(res):
    return [(m["file"], m["page"], d) for d, m in zip(res["documents"][0], res["metadatas"][0])]


def answer(question):
    res = _col.query(query_texts=[question], n_results=N_CANDIDATES)

    # collapse near-identical pages (slide animation frames) into one
    picked = dedupe_pages(_ranked(res), N_PICKED)
    wanted = expand_neighbours(picked, _page_text, NEIGHBORS)

    context = ""
    for file, page in wanted:
        context += f"[{file}, page {page}]\n{_page_text[(file, page)]}\n\n"

    prompt = f"""You answer questions about university course notes.
Use ONLY the excerpts below. After each claim, cite the source like [file, page].
If the excerpts do not contain the answer, say you could not find it in the notes.

Excerpts:
{context}
Question: {question}"""

    msg = _client.messages.create(
        model=MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    USAGE["in"] += msg.usage.input_tokens
    USAGE["out"] += msg.usage.output_tokens
    text = "".join(b.text for b in msg.content if b.type == "text")
    return text, wanted


def search(query, n=6):
    res = _col.query(query_texts=[query], n_results=N_CANDIDATES)
    picked = dedupe_pages(_ranked(res), n)
    return [(f, p, _page_text[(f, p)]) for f, p in picked]


def get_page(file, page):
    return _page_text.get((file, page))
