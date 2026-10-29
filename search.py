import sys
import chromadb

col = chromadb.PersistentClient(path="chroma_db").get_collection("notes")
q = " ".join(sys.argv[1:])
res = col.query(query_texts=[q], n_results=3)
for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
    print(f'--- {meta["file"]}, sayfa {meta["page"]}')
    print(doc[:300].replace("\n", " "))
