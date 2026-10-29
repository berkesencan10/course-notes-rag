import json
import sys
MODE = sys.argv[2] if len(sys.argv) > 2 else "classic"
STATS = []
if MODE == "agent":
    from agent import ask_agent

    def answer(q):
        r, calls = ask_agent(q)
        STATS.append((len(calls), r.get("unverified_sources_removed", 0)))
        text = r["answer"]
        if r["confidence"] == "not_found":
            text = "I could not find this in the notes. " + text
        return text, [(s["file"], s["page"]) for s in r["sources"]]
else:
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
            text, ok = f"ERROR: {e}", False
        passes += ok
        if not ok or not shown_text:
            shown_text = text  # keep a failed answer if there is one
    total += passes
    print(f'{i:2d}. {passes}/{RUNS}  {item["q"]}')
    results.append({"q": item["q"], "passes": passes, "runs": RUNS,
                    "answer": shown_text,
                    "pages": [f"{f} p{p}" for f, p in pages]})

json.dump(results, open(f"eval_results_{MODE}.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
n = len(questions) * RUNS
print(f"\nScore: {total}/{n} ({100 * total / n:.0f}%)")
if STATS:
    print(f"Average tool calls: {sum(c for c, _ in STATS) / len(STATS):.1f}")
    print(f"Unverified sources removed: {sum(r for _, r in STATS)}")

from rag import USAGE
print(f"Tokens per question: input {USAGE['in'] / n:.0f}, output {USAGE['out'] / n:.0f}")
