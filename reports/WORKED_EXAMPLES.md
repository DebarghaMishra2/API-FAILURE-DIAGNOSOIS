# Evidence-backed synthetic worked examples

> All incidents and API documentation are fictional. These examples demonstrate the workflow; they are not HCLTech production incidents or real customer data.

## AUTH-401 — Expired or invalid access token

**Scenario:** A read request is rejected with HTTP 401.

**Classification:** `authentication` (HTTP 401)
**Top-ranked hypothesis:** Authentication failure / invalid or expired credential — high confidence; heuristic score 0.955.
**Metric correlation:** matched (within_window).

**Supporting evidence:**
- Observed HTTP status 401 and classifier signal: HTTP 401 or an explicit authentication/token failure was observed. (source: request/response log)
- Metrics correlated to /v1/orders/{id} (within_window). (source: endpoint metrics)
- Relevant documentation passage: Authentication and Authorization Requirements — Authentication. (source: authentication_and_access.md)
- Relevant documentation passage: Api Error Response Catalogue — Overview. (source: api_error_response_catalogue.pdf)
- Relevant documentation passage: Authentication and Authorization Requirements — Authorization. (source: authentication_and_access.md)

**Contradictory / counter-evidence:**
- No contrary signal for this leading hypothesis was present in the supplied synthetic evidence.

**Documentation evidence retrieved:**
- Authentication and Authorization Requirements — Authentication (authentication_and_access.md): All API requests must use the Bearer [REDACTED] scheme over HTTPS. A 401 response indicates that authentication is missing, invalid, expired, or not accepted by the token issuer. The client should verify token issuer, audience, expiry and the configured authentication scheme using approved identity-
- Api Error Response Catalogue — Overview (api_error_response_catalogue.pdf): API Error Response Catalogue
Version: 1.0
Effective Date: 2026-05-01
Owner: API Reliability Engineering
Status: approved
HTTP 400 / 422 — Request validation
Inspect schema, required fields, JSON types, content type and API version.
HTTP 401 — Authentication
Credentials may be missing, invalid or exp
- Authentication and Authorization Requirements — Authorization (authentication_and_access.md): A 403 response indicates that the authenticated principal is not permitted to perform the requested operation. The Orders API read endpoint requires the `orders:read` scope. A valid token without the required scope can still receive 403. Role or scope changes require an authorized administrator and 

**Safe verification steps:**
- Confirm the authentication scheme and expected key/token identifier without displaying credential values.
- Check issuer, audience, expiry and signing-key metadata in the approved identity-provider console.
- Compare the authentication requirements in the API documentation with the request metadata.

**Still required:**
- Confirm token issuer, audience and expiry using approved identity-provider diagnostics; do not paste token values.
- Check whether the request used the expected authentication scheme and key identifier.

**Important:** This is a probable cause, not a confirmed root cause. Privileged production actions are escalated and are not executed.

## VALID-422 — Order request fails schema validation

**Scenario:** A POST request has an invalid currency field and missing required order items.

**Classification:** `validation` (HTTP 422)
**Top-ranked hypothesis:** Request validation or schema mismatch — high confidence; heuristic score 0.855.
**Metric correlation:** matched (within_window).

**Supporting evidence:**
- Observed HTTP status 422 and classifier signal: A 4xx validation status or a request/schema validation message was observed. (source: request/response log)
- Metrics correlated to /v1/orders (within_window). (source: endpoint metrics)
- Relevant documentation passage: Orders API Reference — POST /v1/orders. (source: orders_api.md)
- Relevant documentation passage: Api Error Response Catalogue — Overview. (source: api_error_response_catalogue.pdf)
- Relevant documentation passage: Orders API Reference — Content type. (source: orders_api.md)

**Contradictory / counter-evidence:**
- No contrary signal for this leading hypothesis was present in the supplied synthetic evidence.

**Documentation evidence retrieved:**
- Orders API Reference — POST /v1/orders (orders_api.md): Creates an order. Required JSON fields are `customer_id` (string), `items` (non-empty array), and `currency` (three-letter uppercase code). Unknown fields are rejected when strict schema validation is enabled. A 400 or 422 response indicates malformed JSON, a missing required field, an invalid field
- Api Error Response Catalogue — Overview (api_error_response_catalogue.pdf): API Error Response Catalogue
Version: 1.0
Effective Date: 2026-05-01
Owner: API Reliability Engineering
Status: approved
HTTP 400 / 422 — Request validation
Inspect schema, required fields, JSON types, content type and API version.
HTTP 401 — Authentication
Credentials may be missing, invalid or exp
- Orders API Reference — Content type (orders_api.md): Requests with JSON payloads must use `Content-Type: application/json`. Confirm the published schema for the deployed API version before changing a client request.

**Safe verification steps:**
- Compare sanitized payload field names and types with the documented schema.
- Check required fields, allowed values, content type and API version.
- Reproduce with a non-production test request after removing sensitive values.

**Still required:**
- Compare sanitized field names and data types with the documented request schema.
- Confirm required fields, allowed enum values and API version.

**Important:** This is a probable cause, not a confirmed root cause. Privileged production actions are escalated and are not executed.

## RATE-429 — API quota exceeded

**Scenario:** A burst of traffic exhausts the per-minute request quota.

**Classification:** `rate_limiting` (HTTP 429)
**Top-ranked hypothesis:** Rate limit or quota exhaustion — high confidence; heuristic score 0.98.
**Metric correlation:** matched (within_window).

**Supporting evidence:**
- Observed HTTP status 429 and classifier signal: HTTP 429 or an explicit rate-limit/quota signal was observed. (source: request/response log)
- HTTP 429 is the standard too-many-requests signal. (source: response status)
- Metrics correlated to /v1/orders (within_window). (source: endpoint metrics)
- Request rate 35 rps is at least 1.8× baseline 8 rps. (source: endpoint metrics)
- A rate-limit remaining header indicates zero remaining quota. (source: response headers)

**Contradictory / counter-evidence:**
- No contrary signal for this leading hypothesis was present in the supplied synthetic evidence.

**Documentation evidence retrieved:**
- Rate Limits — Overview (rate_limits.html): API Rate Limits
API Rate Limits and Quotas
Version: 2.1
Effective Date: 2026-03-01
Owner: API Platform Operations
Status: approved
Product: Acme Public API
Rate limits
When a client exceeds a quota, the API returns HTTP 429 Too Many Requests. Responses may include Retry-After, X-RateLimit-Limit, X-R
- Api Error Response Catalogue — Overview (api_error_response_catalogue.pdf): API Error Response Catalogue
Version: 1.0
Effective Date: 2026-05-01
Owner: API Reliability Engineering
Status: approved
HTTP 400 / 422 — Request validation
Inspect schema, required fields, JSON types, content type and API version.
HTTP 401 — Authentication
Credentials may be missing, invalid or exp
- Webhook Delivery Troubleshooting — Safe checks (webhook_api.md): Confirm the configured destination URL and supported method without exposing query-string secrets. Inspect sanitized response status and retry metadata. Escalate certificate, DNS and destination permission changes to the service owner.

**Safe verification steps:**
- Inspect Retry-After and rate-limit headers, including the quota window and remaining count.
- Compare request rate with the documented limit and correlated endpoint metrics.
- Wait for the indicated reset window or ask the API owner about the applicable quota; avoid retry bursts.

**Still required:**
- Inspect sanitized rate-limit headers, quota window and Retry-After value.
- Confirm the applicable tenant, endpoint and plan-level quota.

**Important:** This is a probable cause, not a confirmed root cause. Privileged production actions are escalated and are not executed.

## TIME-504 — Gateway timeout waiting for order service

**Scenario:** A gateway timeout coincides with elevated endpoint and dependency latency.

**Classification:** `timeout` (HTTP 504)
**Top-ranked hypothesis:** Request or upstream timeout — high confidence; heuristic score 0.98.
**Metric correlation:** matched (within_window).

**Supporting evidence:**
- Observed HTTP status 504 and classifier signal: A timeout status or timeout-related error message was observed. (source: request/response log)
- Metrics correlated to /v1/orders/{id} (within_window). (source: endpoint metrics)
- Endpoint p95 latency is 3200 ms (baseline 150.0 ms). (source: endpoint metrics)
- Relevant documentation passage: Api Error Response Catalogue — Overview. (source: api_error_response_catalogue.pdf)
- Relevant documentation passage: Gateway And Server Errors — Overview. (source: gateway_and_server_errors.txt)

**Contradictory / counter-evidence:**
- No contrary signal for this leading hypothesis was present in the supplied synthetic evidence.

**Documentation evidence retrieved:**
- Api Error Response Catalogue — Overview (api_error_response_catalogue.pdf): API Error Response Catalogue
Version: 1.0
Effective Date: 2026-05-01
Owner: API Reliability Engineering
Status: approved
HTTP 400 / 422 — Request validation
Inspect schema, required fields, JSON types, content type and API version.
HTTP 401 — Authentication
Credentials may be missing, invalid or exp
- Gateway And Server Errors — Overview (gateway_and_server_errors.txt): GATEWAY AND SERVER ERROR GUIDANCE
Version: 1.2
Effective Date: 2026-02-10
Owner: API Reliability Engineering
Status: approved
Product: Acme API Gateway

HTTP 500 Internal Server Error indicates an unexpected server-side condition. Inspect application exception logs and trace spans using a redacted c
- Orders API Reference — Content type (orders_api.md): Requests with JSON payloads must use `Content-Type: application/json`. Confirm the published schema for the deployed API version before changing a client request.

**Safe verification steps:**
- Compare client, gateway and dependency latency for the same timestamp and endpoint.
- Inspect distributed trace spans using the redacted correlation identifier.
- Use a single controlled, non-production reproduction; avoid repeated retries that could amplify load.

**Still required:**
- Inspect distributed trace spans and connect/read timeout boundaries.
- Compare endpoint and downstream dependency latency for the same time window.

**Important:** This is a probable cause, not a confirmed root cause. Privileged production actions are escalated and are not executed.

## SERVER-500 — Unexpected application exception

**Scenario:** A server-side exception is returned without enough trace detail to confirm the root cause.

**Classification:** `server_error` (HTTP 500)
**Top-ranked hypothesis:** Application/server-side failure — high confidence; heuristic score 0.855.
**Metric correlation:** matched (within_window).

**Supporting evidence:**
- Observed HTTP status 500 and classifier signal: An HTTP 5xx response indicates a server-side failure; supplied evidence does not yet isolate the failing component. (source: request/response log)
- Metrics correlated to /v1/orders (within_window). (source: endpoint metrics)
- Endpoint error rate is 7% (>=5% signal threshold). (source: endpoint metrics)
- Relevant documentation passage: Gateway And Server Errors — Overview. (source: gateway_and_server_errors.txt)
- Relevant documentation passage: Api Error Response Catalogue — Overview. (source: api_error_response_catalogue.pdf)

**Contradictory / counter-evidence:**
- No contrary signal for this leading hypothesis was present in the supplied synthetic evidence.

**Documentation evidence retrieved:**
- Gateway And Server Errors — Overview (gateway_and_server_errors.txt): GATEWAY AND SERVER ERROR GUIDANCE
Version: 1.2
Effective Date: 2026-02-10
Owner: API Reliability Engineering
Status: approved
Product: Acme API Gateway

HTTP 500 Internal Server Error indicates an unexpected server-side condition. Inspect application exception logs and trace spans using a redacted c
- Api Error Response Catalogue — Overview (api_error_response_catalogue.pdf): API Error Response Catalogue
Version: 1.0
Effective Date: 2026-05-01
Owner: API Reliability Engineering
Status: approved
HTTP 400 / 422 — Request validation
Inspect schema, required fields, JSON types, content type and API version.
HTTP 401 — Authentication
Credentials may be missing, invalid or exp
- Orders API Reference — Content type (orders_api.md): Requests with JSON payloads must use `Content-Type: application/json`. Confirm the published schema for the deployed API version before changing a client request.

**Safe verification steps:**
- Inspect application exception logs and traces for the same redacted correlation ID.
- Compare error rate and latency before and after relevant deployment/change windows.
- Escalate to the service owner; do not restart services or modify production configuration from this assistant.

**Still required:**
- Inspect server-side exception logs using the redacted correlation ID.
- Check deployment/change events and endpoint error-rate trends for the same period.

**Important:** This is a probable cause, not a confirmed root cause. Privileged production actions are escalated and are not executed.
