import json
import os
import re
import anthropic
import chromadb

MODEL = "claude-sonnet-5-5"
NEIGHBORS = int(os.environ.get("RAG_NEIGHBORS", "1"))  # neighbouring pages added on each side
N_CANDIDATES = 30  # aramadan kaç aday çekilsin
N_PICKED = 6       # benzerleri eledikten sonra kaç sayfa kalsın

_pages = json.load(open("data/pages.json", encoding="utf-8"))
_page_text = {(p["file"], p["page"]): p["text"] for p in _pages}
_col = chromadb.PersistentClient(path="chroma_db").get_collection("notes")
_client = anthropic.Anthropic()
USAGE = {"in": 0, "out": 0}


def _words(text):
    return set(re.findall(r"\w+", text.lower()))


def answer(question):
    res = _col.query(query_texts=[question], n_results=N_CANDIDATES)

    # birbirine çok benzeyen sayfaları (animasyon kareleri) teke indir
    picked, picked_words = [], []
    for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
        w = _words(doc)
        if any(len(w & o) / max(len(w | o), 1) > 0.7 for o in picked_words):
            continue
        picked.append((meta["file"], meta["page"]))
        picked_words.append(w)
        if len(picked) == N_PICKED:
            break

    wanted = set()
    for file, page in picked:
        for k in range(-NEIGHBORS, NEIGHBORS + 1):
            key = (file, page + k)
            if key in _page_text:
                wanted.add(key)
    wanted = sorted(wanted)

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
    picked, picked_words = [], []
    for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
        w = _words(doc)
        if any(len(w & o) / max(len(w | o), 1) > 0.7 for o in picked_words):
            continue
        picked.append((meta["file"], meta["page"]))
        picked_words.append(w)
        if len(picked) == n:
            break
    return [(f, p, _page_text[(f, p)]) for f, p in picked]


def get_page(file, page):
    return _page_text.get((file, page))
