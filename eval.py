import json
import sys
from rag import answer

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 1

NOT_FOUND = ["could not find", "couldn't find", "cannot find", "can't find",
             "did not find", "do not contain", "does not contain",
             "not in the notes", "no information"]


def refused(text):
    head = text[:250].lower()
    return any(p in head for p in NOT_FOUND)


def has_all(text, groups):
    low = text.lower()
    return all(any(alt.strip() in low for alt in g.split("|")) for g in groups)


questions = json.load(open("eval_questions.json", encoding="utf-8"))
results, total = [], 0

for i, item in enumerate(questions, start=1):
    passes, shown_text, pages = 0, "", []
    for _ in range(RUNS):
        try:
            text, pages = answer(item["q"])
            if item["expect"] == "not_found":
                ok = refused(text)
            else:
                ok = (not refused(text)) and has_all(text, item["must"])
        except Exception as e:
            text, ok = f"HATA: {e}", False
        passes += ok
        if not ok or not shown_text:
            shown_text = text  # başarısız bir cevap varsa onu sakla
    total += passes
    print(f'{i:2d}. {passes}/{RUNS}  {item["q"]}')
    results.append({"q": item["q"], "passes": passes, "runs": RUNS,
                    "answer": shown_text,
                    "pages": [f"{f} p{p}" for f, p in pages]})

json.dump(results, open("eval_results.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
n = len(questions) * RUNS
print(f"\nSkor: {total}/{n} ({100 * total / n:.0f}%)")
