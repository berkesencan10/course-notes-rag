# Course Notes Q&A (RAG with citations)

Ask questions about university lecture slides and get answers that cite the **file and page** they came from. If the notes do not contain the answer, the system says so instead of guessing.

A small end-to-end LLM project: PDF extraction, retrieval with a vector store, answer generation with the Claude API, a tool-calling agent with structured JSON output, and an evaluation harness. Built with AI assistance (Claude); each design decision below was tested with the eval harness.

## Example

````
$ python agent.py "Is depth-first search complete?"
````

````json
{
  "answer": "Not in general. Yes for finite acyclic state spaces; yes for finite cyclic spaces if implemented as graph search; no for infinite state spaces.",
  "confidence": "high",
  "sources": [
    {"file": "02_search.pdf", "page": 74},
    {"file": "02_search.pdf", "page": 72}
  ]
}
````
(answer abridged)

For an out-of-scope question ("What is the capital of France?") the agent returns `"confidence": "not_found"` and an empty `sources` list.

## How it works

1. `extract.py` reads every PDF page with PyMuPDF and keeps the file name and page number.
2. `index.py` stores one chunk per page (split at 1500 characters) in a local Chroma database. Embeddings use Chroma's default local model, so no extra API key is needed.
3. Two ways to answer a question:
   - **Classic RAG** (`rag.py`, `ask.py`): vector search, remove near-duplicate pages, add neighbouring pages, then one Claude call with a prompt that says "answer only from the excerpts and cite them".
   - **Agent** (`agent.py`): Claude decides what to do with three tools: `search_notes`, `get_page` and `submit_answer`. The final answer is structured JSON (`answer`, `sources`, `confidence`). Cited pages that the agent never actually read are removed in code.
4. `eval.py` runs a question set against either approach and reports score and token usage.

## Evaluation

23 questions in `eval_questions.json`: 21 about the course content (based on topics from past exams) and 2 out-of-scope questions that must be answered with "not found". Each answer is checked by keyword matching. Each question can be repeated to account for run-to-run variation.

| | Classic RAG | Agent |
|---|---|---|
| Score (23 questions) | 23/23 | 23/23 |
| Input tokens per question | 2379 | 3753 |
| Output tokens per question | 303 | 433 |
| Tool calls per question | none | 2.1 |

The two approaches are equally accurate on this test set. The agent costs about 1.5x more tokens and in return it validates its sources, returns structured JSON and decides itself which pages to read.

## What I learned

- **Slide animation frames flood the search.** One slide deck contains 21 near-identical "Alpha-beta pruning" frames that filled the top results and pushed out the page with the actual algorithm. Removing near-duplicate pages fixed it.
- **Title-only slides.** A slide with only a title is not an answer. Adding neighbouring pages (or letting the agent call `get_page`) fixed several "not found" answers. With 1 neighbouring page the classic version scored 44/46 (96%) because one fact sat two pages away; with 2 it scored 23/23.
- **One eval run is not a score.** The same question passed in one run and failed in the next because the model words answers differently. Repeating each question and averaging is more honest.
- **Check the test, not just the system.** The first baseline was 17/18, but the failure was a keyword check that was too strict (the answer was correct). Two such checks were loosened after reading the answers.

## Limitations

- The test set is small and was written by hand. After the first failures two keyword checks were adjusted, so the 100% is not an unbiased measurement.
- Keyword matching shows that an answer contains the expected terms, not that it is correct. Some checks are loose.
- The test set cannot tell the two approaches apart; a harder set is needed.
- Image-only slides have no extractable text and are skipped (81 of 1319 pages in this course). There is no OCR.
- Diagram slides (for example the alpha-beta worked example) extract as garbled text, so step-by-step explanations of figures are unreliable.
- Tested on one course (14 PDFs, English).

## Setup

````
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"

mkdir -p data/notes        # put your lecture PDFs here
python extract.py          # writes data/pages.json
python index.py            # builds the Chroma index

python ask.py "Explain alpha-beta pruning"        # classic RAG
python agent.py "Is depth-first search complete?" # tool-calling agent

python eval.py 3           # classic, each question 3 times
python eval.py 3 agent     # agent
````

The course PDFs are not included in this repository. `eval_questions.json` was written for an Artificial Intelligence course; replace it with questions for your own notes.
