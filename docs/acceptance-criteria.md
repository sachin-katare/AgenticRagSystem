# Acceptance criteria - fictional advertising corpus

The four files in `sample_data/` describe the fictional LumaWave Ads business. They contain no employer, customer, or personal data.

## Required test journeys

| Test type | File(s) | Question or action | Expected result | Observed response summary | Evidence file | Result |
| --- | --- | --- | --- | --- | --- | --- |
| PDF factual | `policy.pdf` | What approval rules apply to high-risk campaigns? | Legal or compliance review, with approval that may take up to four business days, cited to the campaign-approval section on page 1 | Answered with cited approval rule and up-to-four-business-days limit. | `docs/output-evidence/api/ask-questions/answered/rag/ask-questions-high-risk-approval-response.json` | Passed |
| TXT factual | `notes.txt` | Which advertiser needs server-to-server event mapping validated? | BluePeak Travel, linked to `CMP-002` | Answered BluePeak Travel with citation from the notes corpus. | `docs/output-evidence/api/ask-questions/answered/rag/ask-questions-server-to-server-mapping-response.json` | Passed |
| CSV semantic | `sales.csv` | Which campaign showed creative fatigue? | Returns the creative-fatigue observation and/or the associated campaign identity for GreenFork Market, Fresh Week (`CMP-003`) | Answered with the creative-fatigue observation from the CSV evidence. | `docs/output-evidence/api/ask-questions/answered/rag/ask-questions-creative-fatigue-response.json` | Passed |
| CSV calculation | `sales.csv` | Which campaign had the highest click-through rate? | Identifies Mindful Minutes as highest and gives the calculated rate (11,200 / 350,000 = 3.2%) | Structured route identified Mindful Minutes as highest and returned a 0.032 click-through rate. | `docs/output-evidence/api/ask-questions/answered/structured/ask-questions-highest-click-through-rate-response.json` | Passed |
| CSV calculation | `sales.csv` | Which campaign had the highest return on ad spend? | Identifies Mindful Minutes as highest and gives a return on ad spend of approximately 4.14 | Structured route identified Mindful Minutes as highest and returned approximately 4.14 ROAS. | `docs/output-evidence/api/ask-questions/answered/structured/ask-questions-highest-return-on-ad-spend-response.json` | Passed |
| Excel semantic | `renewals.xlsx` | Which advertiser is concerned about audience saturation? | CloudCart, linked to `REN-007` | Answered CloudCart with citations from the renewals workbook. | `docs/output-evidence/api/ask-questions/answered/rag/ask-questions-audience-saturation-response.json` | Passed |
| Excel calculation | `renewals.xlsx` | Which region has the highest total annual renewal value? | West, with 550,000 dollars | Structured route returned West with a total annual renewal value of 550000.0. | `docs/output-evidence/api/ask-questions/answered/structured/ask-questions-highest-annual-renewal-value-region-response.json` | Passed |
| Excel hybrid | `renewals.xlsx` | How many high-risk renewals mention attribution? | Returns a count of three; naming BluePeak Travel, GreenFork Market, and MetroBank is preferred | Hybrid route returned a count of 3 with route trace showing `hybrid`. | `docs/output-evidence/api/ask-questions/answered/hybrid/ask-questions-high-risk-attribution-count-response.json` | Passed |
| Cross-file trace | `sales.csv` and `renewals.xlsx` | What campaign observation is associated with BluePeak Travel's high-risk renewal? | Returns the attribution/mobile-booking lag or mismatch observation, linked through `CMP-002` | Answered with the attribution/mobile-booking lag observation connected through `CMP-002`. | `docs/output-evidence/api/ask-questions/answered/rag/ask-questions-bluepeak-cross-file-observation-response.json` | Passed |
| Insufficient evidence | All valid files | What is the average age of listeners? | Controlled unsupported or insufficient-evidence response; no source contains listener ages | Returned an insufficient-evidence style answer because no source contains listener ages. | `docs/output-evidence/api/ask-questions/insufficient_evidence/structured/ask-questions-average-listener-age-response.json` | Passed |
| Invalid upload | `malware.exe` or another unsupported extension | Attempt upload | Reject safely with a supported-file-types message; do not store or process it | Upload was rejected safely with a supported-file-types error response. | `docs/output-evidence/api/upload-document/guardrails/upload-unsupported-extension-response.json` | Passed |

## Interpretation notes

- Exact answer wording may vary slightly across reruns for RAG-style questions.
- For semantic/RAG questions, evaluation should focus on whether the answer stays grounded in the source evidence and cites the relevant file/page/row context.
- For structured and hybrid questions, evaluation should focus on the correctness of the returned fact, count, or calculation, even if the response phrasing is more explanatory than the prose above.

## Data-quality checks

- Every identifier is unique within its file.
- Numeric spreadsheet columns are stored as numbers rather than currency-formatted strings.
- Narrative columns exist in both CSV and XLSX for semantic and hybrid retrieval.
- `Last_Campaign_ID` provides explicit cross-file traceability where a prior campaign exists.
- Expected answers above are recalculated during automated tests rather than trusted solely as prose.

## Completion check

The corpus is ready when all four files open successfully, the expected answers above can be reproduced directly from the source content, and the corpus is confirmed to be fictional and safe to use for this project.
