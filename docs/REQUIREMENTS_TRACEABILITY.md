# HCLTech Use Case 4 — Requirements Traceability

The following maps the participant brief to the implementation and test evidence.

| Brief item | Implementation | Evidence / acceptance check |
|---|---|---|
| FR-01 Evidence ingestion | `app/ingestion.py` | JSON/JSONL/CSV logs and metrics; PDF/HTML/MD/TXT docs; source metadata |
| FR-02 Failure classification | `app/classification.py` | `tests/test_classification.py` for auth, authorization, validation, 429, timeout, dependency, server |
| FR-03 Request analysis | `app/request_analysis.py`, `app/redaction.py` | `tests/test_redaction_request.py`; no secret values in analysis/report |
| FR-04 Metric correlation | `app/metrics.py` | `tests/test_metrics.py`; same normalized endpoint and time-window checks |
| FR-05 Documentation retrieval | `app/retrieval.py` | `tests/test_ingestion_retrieval.py`; source/section/page metadata retained |
| FR-06 Ranked diagnosis | `app/diagnosis.py` | `tests/test_diagnosis.py`; support and contradictions emitted; scores marked heuristic |
| FR-07 Safe guidance | `app/guidance.py` | `tests/test_guidance.py`; no destructive actions |
| FR-08 Report and feedback | `app/reporting.py`, `app/feedback.py`, Streamlit feedback form | `tests/test_reporting_feedback.py`; JSON/Markdown reports and SQLite reviewer decisions |
| Working prototype | `streamlit_app.py` | Demo mode and upload mode |
| Evaluation report | `scripts/evaluate.py` | Synthetic results under `reports/`; not a production benchmark |
| Five evidence-backed examples | Seven synthetic cases | `data/synthetic/cases/scenarios.json` and case README |
| Technical documentation | `README.md`, this file, `docs/SAFETY_AND_LIMITATIONS.md` | Setup, inputs, correlation, redaction, trade-offs |

## Known limitations to disclose

- Rules and thresholds are a configurable baseline, not a trained classifier or service-specific calibrated model.
- Metrics correlation is endpoint/time-window based; it is not causal proof.
- BM25 + TF-IDF retrieval is lightweight lexical retrieval, not a transformer semantic retriever.
- Groq narrative generation is optional and may fail; deterministic diagnosis still works.
- Redaction uses patterns and key names; it cannot guarantee removal of every proprietary or customer-specific identifier.
- SQLite feedback is local/ephemeral on common cloud plans unless persistent storage is configured.
- The included synthetic data is fictional and does not establish real-world accuracy.
