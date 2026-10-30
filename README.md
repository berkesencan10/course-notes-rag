# Course Notes Q&A (RAG with citations)

Ask questions about your lecture PDFs and get answers that cite the **file and page** they came from. If the notes do not cover the question, the system says so instead of guessing. Built for students who want to study from their own slides and check every answer against the source.

A small end-to-end LLM project: PDF extraction, retrieval with a local vector store, answer generation with the Claude API, a tool-calling agent with structured JSON output, and an evaluation harness. Built with AI assistance (Claude). Most design decisions were checked with the eval harness, and the pure logic is covered by offline unit tests.

## Example output

A question the notes can answer:

```
$ python -m src.agent "Is depth-first search complete?"
```

```json
{
  "answer": "Not in general. DFS completeness depends on the state space. Yes, for finite, acyclic state spaces. Yes, for finite, cyclic state spaces if it is implemented as graph search (it checks for repeated states). No, for infinite state spaces.",
  "confidence": "high",
  "sources": [
    {"file": "02_search.pdf", "page": 74},
    {"file": "02_search.pdf", "page": 72}
  ],
  "unverified_sources_removed": 0
}
```

A question the notes cannot answer:

```
$ python -m src.agent "What is the capital of France?"
```

```json
{
  "answer": "The notes don't say what the capital of France is. They only cover AI topics such as search, agents, games and machine learning.",
  "sources": [],
  "confidence": "not_found",
  "unverified_sources_removed": 0
}
```

(Real outputs from my test course. The wording differs from run to run; the command also prints the tool calls the agent made.)

## Architecture

```
INDEXING (once)
  PDFs -> extract -> one record per page (file, page, text) -> index -> Chroma

CLASSIC RAG  (src/rag.py)                 AGENT  (src/agent.py)

  question                                  question
     |                                         |
  vector search, top 30                        v
     |                                  +--> Claude --> search_notes
  drop near-duplicate pages             |      |   \--> get_page
     |                                  +------+
  add neighbouring pages                       |
     |                                         v
  one Claude call                        submit_answer (JSON)
     |                                         |
     v                                  drop sources it never saw
  answer + [file, page]                        |
                                               v
                                        answer, sources, confidence
```

Project layout:

```
src/            pipeline code: extract, index, search, rag, ask, agent, helpers
                (helpers.py holds the pure functions that the tests cover)
tests/          offline pytest unit tests (no API calls, no course PDFs)
eval/           eval.py and eval_questions.json
scripts/        check_api.py (checks that your API key works)
data/           created by you: data/notes/ (your PDFs), data/pages.json (git-ignored)
requirements.txt  pinned dependencies
LICENSE         MIT
```

## How it works

1. `src/extract.py` reads every PDF page with PyMuPDF and keeps the file name and page number.
2. `src/index.py` stores one chunk per page in a local Chroma database (a page longer than 1500 characters is split into several chunks; most slide pages are shorter, so they stay as one chunk). Embeddings use Chroma's default local model, so no extra API key is needed.
3. Two ways to answer a question:
   - **Classic RAG** (`src/rag.py`, `src/ask.py`): vector search, remove near-duplicate pages, add neighbouring pages, then one Claude call with a prompt that says "answer only from the excerpts and cite them".
   - **Agent** (`src/agent.py`): Claude decides what to do with three tools: `search_notes`, `get_page` and `submit_answer`. The final answer is structured JSON (`answer`, `sources`, `confidence`). Cited pages that the agent never saw (neither in a search result nor via `get_page`) are removed in code; this never triggered in my tests.
4. `eval/eval.py` runs a question set against either approach and reports score and token usage.

## Why two approaches?

| | Classic RAG | Agent |
|---|---|---|
| Score (23 questions, 1 run each) | 23/23 | 23/23 |
| Input tokens per question | 2379 | 3753 |
| Output tokens per question | 303 | 433 |
| Tool calls per question | none | 2.1 |

On this test set the two are equally accurate. The agent uses about 1.5x the tokens: the input ratio is 1.58 and the output ratio is 1.43, so on the same model it costs roughly 1.4x to 1.6x, whatever the per-token prices are.

My take (a judgment, not something this test measured): classic RAG is the better default. It is one call, cheaper and easier to debug, but its recall depends on retrieval settings (in a separate comparison of 2 runs of 23 questions = 46 checks, 1 neighbouring page scored 44/46 and 2 scored 46/46). The agent is worth its cost when you need structured output or source validation downstream, or when an answer is spread over several places, because it decides what to read. It also has more moving parts: a bad tool call can change the answer.

## Testing

Unit tests cover the logic that does not need the Claude API: splitting text into chunks, near-duplicate removal, removal of unverified sources, neighbour-page expansion and PDF text extraction (the test generates a tiny PDF itself, so no course files are needed). They run offline in about a second:

```
pytest
```

These tests check the code around the model. Answer quality is measured separately by the eval harness below, which calls the API.

## Evaluation

23 questions in `eval/eval_questions.json`: 16 about course topics taken from past exams, 5 about specific details of the lecture slides (written after I had already seen the system's earlier answers, so they are biased towards facts it can find) and 2 out-of-scope questions that must be answered with "not found". Each answer is checked by keyword matching. Each question can be repeated to account for run-to-run variation.

### Adding your own questions

`eval/eval_questions.json` is a list of objects:

```json
{"q": "What is a Horn clause?", "expect": "answer", "must": ["positive|implication|conjunction"]}
{"q": "What is the capital of France?", "expect": "not_found", "must": []}
```

- `expect: "answer"`: the answer must not be a refusal, and every string in `must` must match. Inside one string, alternatives are separated by `|` and one of them is enough. Matching is a case-insensitive substring search.
- `expect: "not_found"`: the answer must say it could not find this in the notes (checked in the first 250 characters).

## What I learned

- **Slide animation frames flood the search.** One slide deck contains 21 near-identical "Alpha-beta pruning" frames that filled the top results and pushed out the page with the actual algorithm. Removing near-duplicate pages fixed it.
- **Title-only slides.** A slide with only a title is not an answer. Adding neighbouring pages (or letting the agent call `get_page`) fixed several "not found" answers. In that comparison (2 runs of the 23 questions = 46 checks) the classic version with 1 neighbouring page scored 44/46 (96%) because one fact sat two pages away; with 2 neighbouring pages (the default, `RAG_NEIGHBORS`) it scored 46/46.
- **One eval run is not a score.** The same question passed in one run and failed in the next because the model words answers differently. Repeating each question and averaging is more honest.
- **Check the test, not just the system.** The first baseline was 17/18, but the failure was a keyword check that was too strict (the answer was correct). Two such checks were loosened after reading the answers.

## Limitations

- The test set is small and was written by hand. After the first failures two keyword checks were adjusted, so the 100% is not an unbiased measurement.
- Keyword matching shows that an answer contains the expected terms, not that it is correct. Some checks are loose.
- The test set cannot tell the two approaches apart; a harder set is needed.
- Image-only slides have no extractable text and are skipped (81 of 1319 pages in this course). There is no OCR.
- Diagram slides (for example the alpha-beta worked example) extract as garbled text, so step-by-step explanations of figures are unreliable.
- Tested on one course (14 PDFs, English).

## Next steps

- OCR for image-only slides.
- A larger and harder test set, with questions written before looking at the system's answers.
- LLM-as-judge scoring next to keyword matching, checked against manual labels.
- A FastAPI service and a Docker image.

## Setup

Run everything from the repository root.

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
python scripts/check_api.py                   # checks that the key works

mkdir -p data/notes                           # put your lecture PDFs here
python -m src.extract                         # writes data/pages.json
python -m src.index                           # builds the Chroma index

python -m src.ask "Explain alpha-beta pruning"          # classic RAG
python -m src.agent "Is depth-first search complete?"   # tool-calling agent

python -m eval.eval 3                         # classic, each question 3 times
python -m eval.eval 3 agent                   # agent

pytest                                        # unit tests, offline
```

The course PDFs are not included in this repository. `eval/eval_questions.json` was written for an Artificial Intelligence course; replace it with questions for your own notes.

## License

MIT, see [LICENSE](LICENSE).
