# Output evidence

This folder contains sanitized evidence showing that the local Agentic RAG System runs successfully with the fabricated/open LumaWave Ads sample corpus.

Request files store the curl commands copied from Swagger UI. Response files store the returned JSON bodies after the matching request is executed.

## Folder layout

```text
output-evidence/
├── api/
│   ├── health-check/
│   ├── upload-document/
│   │   ├── valid/
│   │   └── guardrails/
│   └── ask-questions/
│       ├── answered/
│       │   ├── rag/
│       │   ├── structured/
│       │   └── hybrid/
│       └── insufficient_evidence/
│           └── rag/
├── logs/
└── python-test-output.md
```

The `ask-questions` evidence is grouped by response status first, then by planner route. This makes it easy to verify both the user-visible outcome and the internal route shown in the safe trace.

## Health check

- `api/health-check/health-check-request-curl.txt`
- `api/health-check/health-check-response.json`

## Upload and indexing

Valid upload evidence:

- `api/upload-document/valid/upload-txt-request-curl.txt`
- `api/upload-document/valid/upload-txt-response.json`
- `api/upload-document/valid/upload-pdf-request-curl.txt`
- `api/upload-document/valid/upload-pdf-response.json`
- `api/upload-document/valid/upload-csv-request-curl.txt`
- `api/upload-document/valid/upload-csv-response.json`
- `api/upload-document/valid/upload-xlsx-request-curl.txt`
- `api/upload-document/valid/upload-xlsx-response.json`

Upload guardrail evidence:

- `api/upload-document/guardrails/upload-duplicate-request-curl.txt`
- `api/upload-document/guardrails/upload-duplicate-response.json`
- `api/upload-document/guardrails/upload-empty-request-curl.txt`
- `api/upload-document/guardrails/upload-empty-response.json`
- `api/upload-document/guardrails/upload-unsupported-extension-request-curl.txt`
- `api/upload-document/guardrails/upload-unsupported-extension-response.json`

## Ask questions - answered / RAG route

- `api/ask-questions/answered/rag/ask-questions-audio-ads-request-curl.txt`
- `api/ask-questions/answered/rag/ask-questions-audio-ads-response.json`
- `api/ask-questions/answered/rag/ask-questions-high-risk-approval-request-curl.txt`
- `api/ask-questions/answered/rag/ask-questions-high-risk-approval-response.json`
- `api/ask-questions/answered/rag/ask-questions-attribution-issues-request-curl.txt`
- `api/ask-questions/answered/rag/ask-questions-attribution-issues-response.json`
- `api/ask-questions/answered/rag/ask-questions-server-to-server-mapping-request-curl.txt`
- `api/ask-questions/answered/rag/ask-questions-server-to-server-mapping-response.json`
- `api/ask-questions/answered/rag/ask-questions-creative-fatigue-request-curl.txt`
- `api/ask-questions/answered/rag/ask-questions-creative-fatigue-response.json`
- `api/ask-questions/answered/rag/ask-questions-audience-saturation-request-curl.txt`
- `api/ask-questions/answered/rag/ask-questions-audience-saturation-response.json`
- `api/ask-questions/answered/rag/ask-questions-bluepeak-cross-file-observation-request-curl.txt`
- `api/ask-questions/answered/rag/ask-questions-bluepeak-cross-file-observation-response.json`

## Ask questions - answered / structured route

- `api/ask-questions/answered/structured/ask-questions-highest-revenue-region-request-curl.txt`
- `api/ask-questions/answered/structured/ask-questions-highest-revenue-region-response.json`
- `api/ask-questions/answered/structured/ask-questions-highest-click-through-rate-request-curl.txt`
- `api/ask-questions/answered/structured/ask-questions-highest-click-through-rate-response.json`
- `api/ask-questions/answered/structured/ask-questions-highest-return-on-ad-spend-request-curl.txt`
- `api/ask-questions/answered/structured/ask-questions-highest-return-on-ad-spend-response.json`
- `api/ask-questions/answered/structured/ask-questions-highest-annual-renewal-value-region-request-curl.txt`
- `api/ask-questions/answered/structured/ask-questions-highest-annual-renewal-value-region-response.json`

## Ask questions - answered / hybrid route

- `api/ask-questions/answered/hybrid/ask-questions-high-risk-attribution-count-request-curl.txt`
- `api/ask-questions/answered/hybrid/ask-questions-high-risk-attribution-count-response.json`

## Ask questions - insufficient evidence

- `api/ask-questions/insufficient_evidence/structured/ask-questions-average-listener-age-request-curl.txt`
- `api/ask-questions/insufficient_evidence/structured/ask-questions-average-listener-age-response.json`

## Automated test evidence

- `python-test-output.md`

## Logging evidence

- `logs/app-logging-evidence.txt`
- `logs/error-logging-evidence.txt`
