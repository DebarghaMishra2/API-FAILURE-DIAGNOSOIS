# HCLTech — Intelligent API Failure Diagnosis Assistant

A Streamlit prototype for diagnosing API failures from supplied request/response logs, endpoint metrics, error messages and API documentation. It implements the capabilities in the HCLTech Future Ready AI Engineer Hackathon **Use Case 4** brief.

> **Safety boundary:** The assistant investigates and recommends verification only. It does not call the diagnosed API, modify production systems, rotate credentials, change permissions, raise quotas, restart services or execute recovery. A ranked probable cause is not a confirmed root cause unless supplied evidence establishes it.

## Features mapped to the brief

| Requirement | Implementation |
|---|---|
| FR-01 Evidence ingestion | JSON, JSONL/NDJSON and CSV request/response logs; CSV/JSON metrics; text/structured error messages; PDF, HTML, Markdown and TXT API documentation. Source metadata retained. |
| FR-02 Failure classification | Deterministic classification for authentication, authorization, validation, rate limiting, timeout, dependency and server errors; also explicit not-found/unknown handling. |
| FR-03 Request analysis | Method, normalized endpoint, status, latency, timestamp, correlation ID, header names, safe header allow-list and payload field names/size. Secret values are redacted and payload values are not rendered. |
| FR-04 Metric correlation | Same normalized endpoint and ± configurable time window; p95, error rate, traffic and dependency signals; counter-evidence included. |
| FR-05 Documentation retrieval | BM25 + TF-IDF hybrid retrieval over API docs, preserving title, section, source and PDF page where available. |
| FR-06 Ranked diagnosis | Ranked cause hypotheses with heuristic score, confidence label, supporting evidence, contradictory evidence and missing information. Scores are not probabilities. |
| FR-07 Diagnostic guidance | Category-specific read-only verification steps and escalation notes. No privileged action is executed or recommended as an automatic step. |
| FR-08 Report and feedback | Downloadable JSON/Markdown audit report and reviewer confirm/reject/annotate feedback persisted in local SQLite. |

## Quickstart (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Optional: add GROQ_API_KEY to .env for an LLM-written narrative summary.
streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

The core diagnosis works without a Groq key. Groq is optional and only creates a concise narrative from the deterministic structured findings. The model ID is configurable; default is `openai/gpt-oss-20b` (see the [Groq model catalogue](https://console.groq.com/docs/models)).

## Synthetic demonstrations

Select **Synthetic demo case** in the sidebar. Included scenarios cover:

1. HTTP 401 invalid/expired token (authentication).
2. HTTP 403 missing scope (authorization).
3. HTTP 422 invalid request schema (validation).
4. HTTP 429 exhausted quota (rate limiting).
5. HTTP 504 gateway timeout correlated with elevated upstream latency.
6. HTTP 503 upstream dependency unavailable.
7. HTTP 500 application/server error.
8. Incomplete evidence with no status, timestamp or metrics (unknown/fallback).

Synthetic documents are fictional and intentionally labelled. They are for functional testing only, not statements about HCLTech or any real API.

## Upload formats

### Request/response logs
- `.json`: one object, array, or an object containing `records`, `logs`, `requests`, `responses` or `events`.
- `.jsonl` / `.ndjson`: one JSON object per line.
- `.csv`: one record per row.

Recognized common aliases include `http_method`/`verb`, `url`/`path`/`route`, `status`/`http_status`, `duration_ms`/`response_time_ms`, `request_id`/`trace_id`, and `time`/`ts`.

A log record may contain top-level request/response objects or a flattened record. Request and response events can be joined by correlation ID when supplied.

Example flattened record:

```json
{
  "timestamp": "2026-11-14T09:15:00Z",
  "method": "GET",
  "endpoint": "/v1/orders",
  "status_code": 429,
  "latency_ms": 12,
  "correlation_id": "CORR-1234",
  "request_headers": {"Authorization": "Bearer do-not-share"},
  "response_headers": {"Retry-After": "30", "X-RateLimit-Remaining": "0"},
  "error_message": "Too many requests"
}
```

### Endpoint metrics
CSV/JSON/JSONL with endpoint and timestamp plus any of:
`p95_latency_ms`, `error_rate_pct`, `request_rate_rps`, `dependency_error_rate_pct`, `dependency_p95_latency_ms`.

Metrics are correlated only when normalized endpoint matches and timestamps are within the configured ±300 second window. If either timestamp is missing, a same-endpoint match may be shown as `time_unknown`; it is not treated as a verified time correlation.

### Error messages
TXT or structured JSON/JSONL/CSV. Error text is redacted and truncated for display.

### API documentation
PDF, HTML, HTM, Markdown and TXT. Ingestion preserves source file, title, section and PDF page where available. PDF table extraction uses `pdfplumber`; extraction quality depends on document layout. Scanned PDFs without text are not OCRed in this starter and should be converted/OCRed before upload.

## Security and redaction

- Redacts fields whose names contain authorization, cookie, password, secret, API key, token or credential indicators.
- Redacts common Bearer strings, JWT-like values, common API-key prefixes, private-key blocks and email addresses in text.
- Request analysis displays header **names** and a small allow-list of non-sensitive header values; it does not display raw bodies. It displays payload field names and byte size only.
- Redaction is best-effort, not a substitute for upstream log scrubbing or a data-loss prevention gateway. Review sanitized output before sharing reports.
- Do not upload production secrets, full customer payloads or data you are not authorized to process.

## Diagnosis methodology

1. Deterministic rules classify the failure from status and error signatures.
2. Request analysis extracts metadata without displaying secret values.
3. Metrics are joined by normalized endpoint and time window.
4. API-doc passages are retrieved with BM25 + TF-IDF lexical retrieval.
5. A rule-based ranker scores likely causes using request, metrics and docs evidence. Each candidate includes support, counter-evidence and information still required.
6. A category-specific safe guidance list is attached.
7. Optional Groq narrative summarizes the structured result. It cannot replace or silently alter the deterministic result.
8. The audit report is exported as JSON or Markdown; reviewers can confirm, reject or annotate the top hypothesis.

### Score and uncertainty limitations

Diagnosis scores and high/medium/low labels are **heuristic ranking indicators**, not calibrated probabilities. The app never labels the root cause confirmed by default. Metric thresholds (for example, 5% error rate or 1000 ms p95 latency) are demo heuristics and should be adapted to each service's SLOs. Missing timestamps, missing IDs, sparse metrics and missing documentation are surfaced as uncertainty.

## Evaluation

Run the included synthetic smoke evaluation:

```bash
python scripts/evaluate.py
```

Outputs:
- `reports/synthetic_evaluation.json`
- `reports/SYNTHETIC_EVALUATION.md`

Metrics include classification accuracy, expected diagnosis top-1/top-3, and same-endpoint metric correlation rate. The included scenarios are synthetic and small. These figures are **functional smoke-test results, not independent benchmark or production accuracy claims**. For submission, add a manually labelled held-out dataset and evaluate classification confusion matrix, MRR/nDCG of diagnosis ranking, evidence-correlation accuracy, safe-guidance review, redaction checks and uncertainty handling.

Run automated tests:

```bash
python -m unittest discover -s tests -v
```

## Deployment

### Streamlit Community Cloud
- Push the project to GitHub.
- Create a Streamlit app with main file `streamlit_app.py`.
- Add `GROQ_API_KEY` and `GROQ_MODEL` in App Settings → Secrets (TOML format). The key is optional; without it deterministic findings still work.

### Docker / Render

```bash
docker build -t hcltech-api-diagnosis .
docker run -p 8501:8501 -e GROQ_API_KEY="$GROQ_API_KEY" hcltech-api-diagnosis
```

A `render.yaml` Blueprint and `Dockerfile` are included. Set `GROQ_API_KEY` as a secret in the Render service environment; never commit `.env`. Render's default filesystem is ephemeral, so SQLite feedback may not survive a redeploy/restart. For durable reviewer feedback, attach a persistent disk or use a managed database and update `FEEDBACK_DB_PATH` accordingly.

## Project layout

```text
app/                 ingestion, redaction, classifier, correlation, retrieval, ranking, guidance, reporting, feedback
 data/synthetic/     synthetic cases and API docs
 evaluation/         test case manifest
 reports/            synthetic evaluation outputs
 scripts/            evaluation and demo runners
 tests/              unit and integration tests
 streamlit_app.py    reviewer-facing UI
```

## Scope boundaries

The solution diagnoses and recommends verification. Production API changes, credential operations and automated recovery are deliberately out of scope, in line with the participant brief. A probable cause must not be presented as confirmed root cause unless the supplied evidence establishes it.
