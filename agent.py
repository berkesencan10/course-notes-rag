import sys
import json
import anthropic
from rag import search, get_page, MODEL, USAGE

SYSTEM = """You answer questions about university course notes (lecture slides).
Use search_notes to find relevant pages. Slide titles often appear alone, so use get_page
to read neighbouring pages when a result looks like only a title.
Use ONLY the notes, never your own knowledge.
When you are done, call submit_answer. If the notes do not contain the answer,
call submit_answer with confidence "not_found" and an empty sources list.
Only cite pages you actually read."""

TOOLS = [
    {
        "name": "search_notes",
        "description": "Search the course notes. Returns the most relevant pages with file name, page number and text.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_page",
        "description": "Read one specific page of a notes file.",
        "input_schema": {
            "type": "object",
            "properties": {"file": {"type": "string"}, "page": {"type": "integer"}},
            "required": ["file", "page"],
        },
    },
    {
        "name": "submit_answer",
        "description": "Submit the final answer. Call this exactly once, when finished.",
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"file": {"type": "string"}, "page": {"type": "integer"}},
                        "required": ["file", "page"],
                    },
                },
                "confidence": {"type": "string", "enum": ["high", "medium", "low", "not_found"]},
            },
            "required": ["answer", "sources", "confidence"],
        },
    },
]

_client = anthropic.Anthropic()
_seen = set()


def run_tool(name, args):
    if name == "search_notes":
        hits = search(args["query"])
        _seen.update((f, p) for f, p, _ in hits)
        return "\n\n".join(f"[{f}, page {p}]\n{t[:1200]}" for f, p, t in hits)
    if name == "get_page":
        t = get_page(args["file"], args["page"])
        if t:
            _seen.add((args["file"], args["page"]))
        return t if t else "No text on that page (it may be an image or out of range)."
    return "Unknown tool."


def ask_agent(question, max_steps=8):
    _seen.clear()
    messages = [{"role": "user", "content": question}]
    calls = []
    for _ in range(max_steps):
        resp = _client.messages.create(
            model=MODEL, max_tokens=4000, system=SYSTEM,
            tools=TOOLS, messages=messages,
        )
        USAGE["in"] += resp.usage.input_tokens
        USAGE["out"] += resp.usage.output_tokens
        messages.append({"role": "assistant", "content": resp.content})
        tool_uses = [b for b in resp.content if b.type == "tool_use"]
        if not tool_uses:
            text = "".join(b.text for b in resp.content if b.type == "text")
            return {"answer": text, "sources": [], "confidence": "low"}, calls
        results = []
        for tu in tool_uses:
            if tu.name == "submit_answer":
                out = dict(tu.input)
                kept = [s for s in out.get("sources", []) if (s["file"], s["page"]) in _seen]
                out["unverified_sources_removed"] = len(out.get("sources", [])) - len(kept)
                out["sources"] = kept
                return out, calls
            calls.append((tu.name, tu.input))
            results.append({"type": "tool_result", "tool_use_id": tu.id,
                            "content": run_tool(tu.name, tu.input)})
        messages.append({"role": "user", "content": results})
    return {"answer": "Step limit reached.", "sources": [], "confidence": "low"}, calls


if __name__ == "__main__":
    result, calls = ask_agent(" ".join(sys.argv[1:]))
    print("Tool calls:")
    for name, args in calls:
        print(f"  {name}({json.dumps(args, ensure_ascii=False)})")
    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))
