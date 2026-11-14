# Safety, Redaction and Limitations

## Strictly diagnostic scope

The assistant is read-only. It does not send requests to the diagnosed API or perform credential reset, role/scope changes, quota changes, production configuration changes, service restarts or automated remediation. Privileged operations are escalated to authorized owners.

## Redaction

Sensitive field names and common token patterns are redacted before analysis and reporting. Raw payload values are not rendered by the UI. However pattern-based redaction can miss novel credential formats, encoded secrets, proprietary identifiers or sensitive values under unexpected field names. The uploader warns users to submit only authorized, sanitized data. Organizations should additionally scrub logs upstream and apply their own data-loss-prevention rules.

## Uncertainty and causal claims

HTTP status and error text can identify a failure class but rarely prove the underlying root cause. A 500, 503 or timeout may have multiple causes. Metrics at the same endpoint and time can support or weaken hypotheses but do not prove causality. Scores are heuristic and not probabilities. The report's `root_cause_confirmed` field is false unless a future human-reviewed workflow is explicitly added; this starter does not set it true.

## Evaluation limits

Seven synthetic scenarios cover the required failure families. They are not representative of production distribution. The scripted evaluation reports only synthetic classification and ranking smoke metrics. A final hackathon report should include a held-out, manually labelled dataset and review of evidence correlation and guidance quality.

## Cloud storage

Uploads are held in memory for the current Streamlit session. SQLite feedback is written locally. Some cloud hosts use ephemeral filesystems; use persistent storage or a managed database if feedback must survive restarts. No production log upload retention policy is implemented.
