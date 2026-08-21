# Agentic RAG System

Local capstone application for document ingestion, retrieval-augmented question answering, deterministic table analysis, and LangGraph-style agent orchestration.

The system runs fully on a local machine using FastAPI, Streamlit, Ollama, ChromaDB, and pandas. It supports PDF, TXT, CSV, and XLSX uploads.

## Repository location

[https://github.com/sachin-katare/AgenticRagSystem](https://github.com/sachin-katare/AgenticRagSystem)

## What this project does

The application lets a user:

- upload supported documents
- index them locally for retrieval
- ask grounded natural-language questions
- review answers together with status, trace, and source evidence

It combines two styles of question handling:

- semantic document QA through embeddings and vector search
- deterministic table analysis for supported CSV/XLSX questions

## UI sneak peek

Upload flow:

![Upload flow](<docs/output-evidence/ui/upload-document/Upload Document Response.png>)

Ask-questions flow:

![Ask questions flow](<docs/output-evidence/ui/ask-questions/Ask Question Response.png>)

## Current scope

Included in this repository:

- local FastAPI API
- local Streamlit UI
- local Ollama chat and embedding models
- local ChromaDB vector store
- local document registry
- LangGraph-style six-role workflow for question answering
- visible output evidence under [`docs/output-evidence`](docs/output-evidence)

Requirement/source mapping for this capstone is documented in [`docs/source-traceability.md`](docs/source-traceability.md).

Intentionally out of scope for this capstone version:

- cloud deployment
- authentication and user accounts
- OCR and image ingestion
- web browsing or external tools from the model
- production-grade multi-user scaling

## Main user flow

1. Start Ollama.
2. Start the FastAPI service.
3. Start the Streamlit UI.
4. Upload one or more supported documents.
5. Ask a question through the UI or `POST /ask-questions`.
6. Review the answer, status, agent trace, and citations.

## Supported document types

- PDF
- TXT
- CSV
- XLSX

The current sample corpus used for demonstration is a fabricated advertising-governance dataset with:

- policy-style PDF content
- plain text notes
- structured sales CSV data
- renewal workbook data with both numeric and text-bearing fields

## High-level architecture

```text
Streamlit UI --> FastAPI API --> Ingestor --> Document registry JSON
                   |              |
                   |              +-------> ChromaDB (chunks + vectors)
                   |
                   +--> LangGraph workflow
                        Validator --> Planner --> Retriever/structured tool
                                              --> Reasoner --> Responder --> Validator

Ollama models:
- nomic-embed-text for embeddings
- llama3.2:3b for grounded answer generation
```

## Main components

### Ingestion path

When a file is uploaded, the system:

1. validates the file type and size
2. saves the file safely
3. extracts text or table content
4. chunks the extracted content
5. creates embeddings
6. stores vectors in ChromaDB
7. stores document metadata in the local document registry

### Question-answering path

When a question is asked, the system:

1. validates the question
2. plans a route
3. retrieves evidence or runs deterministic table analysis
4. reasons only over the returned evidence/result
5. writes the response
6. validates the final output before returning it

## Client-facing endpoints

These are the main user-facing endpoints:

- `GET /health-check` — verifies the local API and model configuration
- `POST /upload-document` — uploads, extracts, chunks, embeds, indexes, and registers a document
- `POST /ask-questions` — runs the agent workflow and returns an answer, status, trace, and citations when applicable

Developer/debug endpoints also exist for local learning and manual inspection, but the intended client flow is centered on the three endpoints above.

## Agent roles

The project uses six explicit roles in the question-answering workflow:

| Role | Responsibility |
| --- | --- |
| Ingestor | prepares uploaded content for retrieval and structured use |
| Retriever | retrieves semantic evidence from ChromaDB |
| Planner | chooses the route for the question |
| Reasoner | interprets evidence or deterministic results |
| Responder | formats the user-facing answer |
| Validator | checks inputs and final outputs for safety and consistency |

The ingestion role is part of upload-time processing. The LangGraph-style question workflow is used during `/ask-questions`.

## Route meanings

The `/ask-questions` response includes a safe trace such as:

```json
[
  "Validator(input)",
  "Planner(route=rag)",
  "Retriever",
  "Reasoner",
  "Responder",
  "Validator(output)"
]
```

The planner route explains how the question was handled:

| Route | Meaning | Example |
| --- | --- | --- |
| `rag` | semantic vector retrieval plus grounded answer generation with citations | `What rules apply to audio ads?` |
| `structured` | deterministic table calculation over uploaded CSV/XLSX data | `Which region has the highest revenue?` |
| `hybrid` | semantic text condition plus deterministic filtering/counting over table data | `How many high-risk renewals mention attribution issues?` |
| `clarification` | the question is too vague or unsupported for a safe route | `Tell me about data` |

## Status meanings

`status` describes the outcome, not the route.

Common `/ask-questions` statuses include:

- `answered`
- `insufficient_evidence`
- `citation_validation_failed`
- `clarification`

For example, a response may have:

- `status = answered`
- `trace` containing `Planner(route=structured)`

That means the question was answered successfully through the structured-analysis route.

## Evidence and citations

The project is designed to keep answers grounded in retrieved evidence or deterministic calculation results.

For RAG-style answers, responses include:

- answer text
- citation count
- citation objects
- safe agent trace

Citations include source metadata such as:

- filename
- page number for PDF evidence
- sheet and row details for workbook evidence
- chunk metadata used during retrieval

## Safety and reliability features

Implemented safeguards include:

- allowed-extension validation
- file-size validation
- empty-question validation
- duplicate-upload detection using content hashes
- friendly `503` handling for local model/service failures
- rotating application and error logs
- log redaction so prompts, full document bodies, and secrets are not written to logs
- output validation for citation consistency
- insufficient-evidence handling instead of unsupported guessing

## Structured-analysis limitation

The deterministic table-analysis path is intentionally narrower than the RAG path.

It currently works best for uploaded CSV/XLSX questions that can be answered through:

- direct numeric aggregation such as counts, sums, averages, highest, and lowest
- a small set of built-in derived business metrics such as click-through rate, return on ad spend, and conversion rate
- hybrid questions that combine exact filters with a semantic term

It is not a general spreadsheet reasoning engine. For unrelated domains or arbitrary custom formulas, `/ask-questions` will use `rag` whenever deterministic table analysis cannot support the question, or the deterministic analysis layer would need extension.

## Technology stack

- Python 3.11
- FastAPI
- Streamlit
- Ollama
- ChromaDB
- pandas
- pypdf
- openpyxl
- LangGraph
- pytest

Why these libraries and framework choices were made is documented in [`docs/dependency-decisions.md`](docs/dependency-decisions.md).

## Local setup

### 1. Create and activate the virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Start Ollama and pull the local models

```powershell
ollama pull llama3.2:3b
ollama pull nomic-embed-text
ollama serve
```

### 3. Start the API

```powershell
uvicorn app.api.main:app --reload --port 8000
```

### 4. Start the UI

```powershell
streamlit run app/ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

### 5. Open the local interfaces

- FastAPI docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Streamlit UI: [http://127.0.0.1:8501](http://127.0.0.1:8501)

## Testing

Run the automated suite from the project root:

```powershell
python -m pytest -q tests
```

The current project evidence also includes saved pytest output in [`docs/output-evidence/python-test-output.md`](docs/output-evidence/python-test-output.md).

Testable success cases and their matching evidence files are summarized in [`docs/acceptance-criteria.md`](docs/acceptance-criteria.md).

## Project evidence

Public verification artifacts are stored in:

```text
docs/output-evidence/
```

That folder contains public verification artifacts such as API request/response evidence, test-output evidence, log samples, and any saved UI evidence used to demonstrate the system behavior.

For the evidence layout and file-by-file guide, see [`docs/output-evidence/README.md`](docs/output-evidence/README.md).

## Repository guidance for new contributors

If you are new to this project, the best way to onboard is:

1. read this README
2. start the local stack
3. upload the sample documents
4. try one RAG question, one structured table question, and one hybrid question
5. inspect the returned `status`, `trace`, and citations

That gives the fastest understanding of how the ingestion, retrieval, deterministic analysis, and agent orchestration fit together.

## Known design choices

- The application is local-first and intentionally simple to run.
- The question-answering workflow is bounded and traceable rather than autonomous.
- Deterministic analysis is preferred for supported exact tabular questions.
- RAG is preferred for generic semantic document questions.
- Public cloud deployment is intentionally deferred in this capstone version.

## Development challenges

Key implementation challenges during this capstone included:

- keeping answers grounded with citations instead of letting the local model answer too freely
- separating semantic retrieval from deterministic table analysis so numeric questions stay verifiable
- making the LangGraph-style workflow traceable without exposing chain-of-thought
- preventing runtime artifacts such as logs, uploads, ChromaDB data, and private notes from leaking into the final ZIP
- keeping the local Streamlit demo stable and readable enough for a submission walkthrough
