# HCLTech Use Case 4 — Submission Checklist

- [x] Accept request/response logs (JSON, JSONL, CSV).
- [x] Accept endpoint metrics (CSV, JSON).
- [x] Accept error messages/stack excerpts.
- [x] Accept API documentation (PDF, HTML, Markdown, TXT).
- [x] Preserve source, title, section, page and document metadata where available.
- [x] Classify authentication, authorization, validation, rate-limit, timeout, dependency and server errors.
- [x] Analyze method, endpoint, status, latency, safe header metadata, payload field names and correlation ID without rendering secret values.
- [x] Correlate same normalized endpoint and time window; surface anomalies and counter-evidence.
- [x] Retrieve API-doc requirements and troubleshooting passages.
- [x] Rank likely causes with support, counter-evidence, heuristic confidence and remaining information.
- [x] Recommend read-only/non-destructive checks and escalation for privileged actions.
- [x] Export JSON/Markdown reports and capture reviewer confirm/reject/annotate feedback.
- [x] Include at least five worked examples (401, 422, 429, 504, 500).
- [x] Include synthetic evaluation and limitations.
- [ ] Replace/augment synthetic records with HCLTech-supplied permitted data, if provided.
- [ ] Run a manual review with held-out cases and capture screenshots from the actual deployment environment.

The last two items require participant-side source data and human review; they cannot be truthfully marked complete by an offline code package.
