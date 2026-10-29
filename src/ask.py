"""Command line: answer one question with classic RAG and list the pages used."""
import sys
from src.rag import answer

text, pages = answer(" ".join(sys.argv[1:]))
print(text)
print("\nPages consulted:")
for f, p in pages:
    print(f"  - {f}, page {p}")
