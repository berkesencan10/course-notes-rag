import json
import chromadb

pages = json.load(open("data/pages.json", encoding="utf-8"))

client = chromadb.PersistentClient(path="chroma_db")
try:
    client.delete_collection("notes")
except Exception:
    pass
col = client.create_collection("notes")

ids, docs, metas = [], [], []
for p in pages:
    text = p["text"]
    parts = [text[i:i + 1500] for i in range(0, len(text), 1500)]
    for j, part in enumerate(parts):
        ids.append(f'{p["file"]}-p{p["page"]}-{j}')
        docs.append(part)
        metas.append({"file": p["file"], "page": p["page"]})

for i in range(0, len(ids), 500):
    col.add(ids=ids[i:i + 500], documents=docs[i:i + 500], metadatas=metas[i:i + 500])
    print(f"{min(i + 500, len(ids))}/{len(ids)}")

print(len(ids), "chunks indexed")
