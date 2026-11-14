# Synthetic API failure scenarios

All records are fictional and contain no real credentials or customer data. They cover HTTP 401, 403, 422, 429, 504, 503 and 500, including the five mandatory demonstration categories in the HCLTech brief. Expected labels are documented in `scenarios.json`. The data is designed for repeatable functional testing, not production performance claims.

| Case | Expected category | Main evidence | Still needed |
|---|---|---|---|
| AUTH-401 | authentication | 401 invalid/expired bearer token | IdP issuer/audience/expiry validation |
| AUTHZ-403 | authorization | 403 insufficient scope | principal role and scope audit |
| VALID-422 | validation | 422 field validation | deployed schema/version confirmation |
| RATE-429 | rate_limiting | 429, Retry-After, zero quota, traffic spike | tenant plan/quota confirmation |
| TIME-504 | timeout | 504 and elevated endpoint/dependency latency | distributed trace spans |
| DEP-503 | dependency_error | 503, upstream connection refused, dependency errors | dependency owner/health confirmation |
| SERVER-500 | server_error | 500 and elevated error rate | server exception trace |
| UNKNOWN-008 | unknown / insufficient evidence | generic error only; no status, time, metrics or relevant docs | sanitized response log, timestamp, metrics and API contract |
