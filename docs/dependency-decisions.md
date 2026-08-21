# Dependency decisions

This project uses direct dependencies that are compatible with the local-first architecture.

- Use `requirements.txt`, matching the conventional Python dependency filename.
- Use `python-dotenv` instead of the ambiguous `dotenv` package name.
- Use Python's built-in `logging` package for application and error logging.
- Use `langchain-ollama` instead of cloud-oriented OpenAI packages because Ollama is the selected local model provider.
- Add ChromaDB, openpyxl, multipart upload support, LangGraph, pytest, and Ruff because the chosen architecture needs them.
- Capture the exact working transitive versions in `requirements-resolved.txt` only after installation succeeds.

The initial direct versions remain hypotheses until `pip check`, imports, and project tests pass together on Python 3.11.
