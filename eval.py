import json
from rag import answer

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
results, passed = [], 0

for i, item in enumerate(questions, start=1):
    try:
        text, pages = answer(item["q"])
        if item["expect"] == "not_found":
            ok = refused(text)
        else:
            ok = (not refused(text)) and has_all(text, item["must"])
    except Exception as e:
        text, pages, ok = f"HATA: {e}", [], False
    passed += ok
    print(f'{i:2d}. {"PASS" if ok else "FAIL"}  {item["q"]}')
    results.append({"q": item["q"], "ok": ok, "answer": text,
                    "pages": [f"{f} p{p}" for f, p in pages]})

json.dump(results, open("eval_results.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(f"\nSkor: {passed}/{len(questions)}")
