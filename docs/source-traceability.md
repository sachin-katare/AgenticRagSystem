# Source traceability

This document records why implementation decisions exist and links them to the implemented system behavior.

| Decision | Primary basis | Implementation evidence |
| --- | --- | --- |
| Support PDF, TXT, CSV, and XLSX | Project requirements for mixed document and spreadsheet ingestion | Four fabricated files under `sample_data/` |
| Use fixed-size and overlapping chunking | Retrieval quality, chunk-boundary control, and local validation experiments | Adaptive chunking policy and `tests/test_chunking.py` |
| Store embeddings and metadata in ChromaDB | Local vector retrieval and persistent semantic search requirements | `app/services/vector_store.py` and persistence tests |
| Return source citations and refuse unsupported answers | Grounding, verification, and safe-answering requirements | RAG, Validator, and citation tests |
| Use deterministic calculations for exact tabular questions | Exact numeric-answer reliability and spreadsheet-analysis requirements | pandas/openpyxl analysis tool and structured-analysis tests |
| Use six explicit roles | Agent-oriented workflow design and traceable orchestration requirements | Ingestor, Planner, Retriever, Reasoner, Responder, and Validator graph nodes |
