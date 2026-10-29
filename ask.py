import sys
from rag import answer

text, pages = answer(" ".join(sys.argv[1:]))
print(text)
print("\nPages consulted:")
for f, p in pages:
    print(f"  - {f}, page {p}")
