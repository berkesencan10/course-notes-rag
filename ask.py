import sys
import json
import re
import anthropic
import chromadb

question = " ".join(sys.argv[1:])

pages = json.load(open("data/pages.json", encoding="utf-8"))
page_text = {(p["file"], p["page"]): p["text"] for p in pages}


def words(text):
    return set(re.findall(r"\w+", text.lower()))


col = chromadb.PersistentClient(path="chroma_db").get_collection("notes")
res = col.query(query_texts=[question], n_results=30)

# birbirine çok benzeyen sayfaları (animasyon kareleri) teke indir
picked, picked_words = [], []
for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
    w = words(doc)
    if any(len(w & o) / max(len(w | o), 1) > 0.7 for o in picked_words):
        continue
    picked.append((meta["file"], meta["page"]))
    picked_words.append(w)
    if len(picked) == 6:
        break

# her sayfanın 1 önceki ve 1 sonraki sayfasını da al
wanted = set()
for file, page in picked:
    for k in range(-1, 2):
        key = (file, page + k)
        if key in page_text:
            wanted.add(key)

context = ""
for file, page in sorted(wanted):
    context += f"[{file}, page {page}]\n{page_text[(file, page)]}\n\n"

prompt = f"""You answer questions about university course notes.
Use ONLY the excerpts below. After each claim, cite the source like [file, page].
If the excerpts do not contain the answer, say you could not find it in the notes.

Excerpts:
{context}
Question: {question}"""

client = anthropic.Anthropic()
msg = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=3000,
    messages=[{"role": "user", "content": prompt}],
)

print("".join(b.text for b in msg.content if b.type == "text"))
print("\nBakılan sayfalar:")
for file, page in sorted(wanted):
    print(f"  - {file}, sayfa {page}")
