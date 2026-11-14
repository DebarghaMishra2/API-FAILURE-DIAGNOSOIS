# Synthetic API Failure Diagnosis Evaluation

> This is a deterministic smoke evaluation over included fictional scenarios; it is not a real-world benchmark or evidence of production accuracy.

- Cases: 8
- Classification accuracy: 100.0%
- Expected diagnosis ranked #1: 100.0%
- Expected diagnosis in top 3: 100.0%
- Metric correlation rate: 87.5%

| Case | Expected | Predicted | Class correct | Expected diagnosis top 1 |
|---|---|---|---:|---:|
| AUTH-401 | authentication | authentication | Yes | Yes |
| AUTHZ-403 | authorization | authorization | Yes | Yes |
| VALID-422 | validation | validation | Yes | Yes |
| RATE-429 | rate_limiting | rate_limiting | Yes | Yes |
| TIME-504 | timeout | timeout | Yes | Yes |
| DEP-503 | dependency_error | dependency_error | Yes | Yes |
| SERVER-500 | server_error | server_error | Yes | Yes |
| UNKNOWN-008 | unknown | unknown | Yes | Yes |

## Scenario coverage

The suite includes 4xx validation, 5xx server, authentication, authorization, rate limiting, timeout and dependency failure cases. It also includes an incomplete/unsupported case with no status, timestamp, metrics or applicable docs; the expected behaviour is an `unknown` classification with information still required.

## Observed errors

- No classification mismatch occurred in this deterministic synthetic run.
- Unsupported/incomplete cases correctly classified as unknown: 1/1.
- The automated test suite covers parser formats, redaction, metric endpoint/time joins, documentation retrieval, report export, diagnosis ranking and reviewer feedback.

## Limitations

- The synthetic set is small and deliberately explicit; results are not a generalization estimate or production accuracy claim.
- Cause scores/confidence labels and metric thresholds are heuristic, not calibrated probabilities or service-specific SLO thresholds.
- Metric correlation is not proof of causality; missing/late metrics and clock skew can weaken conclusions.
- BM25 + TF-IDF is lightweight lexical retrieval and can miss paraphrases with low term overlap.
- Redaction is pattern-based best effort; inspect outputs and scrub source logs upstream.
- A human reviewer must confirm/reject diagnoses before operational action; this assistant executes no remediation.

