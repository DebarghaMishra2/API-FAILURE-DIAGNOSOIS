"""Safe, non-destructive diagnostic guidance by failure class."""
GUIDANCE={
 "authentication": ["Confirm the authentication scheme and expected key/token identifier without displaying credential values.","Check issuer, audience, expiry and signing-key metadata in the approved identity-provider console.","Compare the authentication requirements in the API documentation with the request metadata."],
 "authorization": ["Verify the caller's assigned role and required scopes with the API owner.","Check tenant, resource and environment-specific access policy using read-only administrative views.","Escalate permission changes to an authorized administrator; do not alter roles or scopes from this assistant."],
 "validation": ["Compare sanitized payload field names and types with the documented schema.","Check required fields, allowed values, content type and API version.","Reproduce with a non-production test request after removing sensitive values."],
 "rate_limiting": ["Inspect Retry-After and rate-limit headers, including the quota window and remaining count.","Compare request rate with the documented limit and correlated endpoint metrics.","Wait for the indicated reset window or ask the API owner about the applicable quota; avoid retry bursts."],
 "timeout": ["Compare client, gateway and dependency latency for the same timestamp and endpoint.","Inspect distributed trace spans using the redacted correlation identifier.","Use a single controlled, non-production reproduction; avoid repeated retries that could amplify load."],
 "dependency_error": ["Inspect upstream dependency health and corresponding trace/span failures.","Check whether other endpoints using the same dependency show correlated errors.","Escalate to the dependency owner with timestamp, endpoint and redacted correlation ID."],
 "server_error": ["Inspect application exception logs and traces for the same redacted correlation ID.","Compare error rate and latency before and after relevant deployment/change windows.","Escalate to the service owner; do not restart services or modify production configuration from this assistant."],
 "not_found": ["Confirm HTTP method, base URL, route template and API version.","Check whether the resource exists in the intended tenant/environment using read-only queries.","Compare the endpoint path with the published API specification."],
 "unknown": ["Collect a sanitized request/response record with timestamp, method, endpoint, status and latency.","Provide endpoint metrics for the same endpoint and time window.","Attach the relevant API documentation and error message after removing secrets."],
}
PRIVILEGED_ESCALATION="Any credential reset, permission change, quota increase, production configuration change, service restart or recovery action must be performed by an authorized operator under the organization's change-control process. This assistant only recommends verification and escalation; it does not execute changes."

def diagnostic_guidance(category):
    return {"verification_steps":GUIDANCE.get(category,GUIDANCE["unknown"]),"escalation":PRIVILEGED_ESCALATION,"automation_performed":False,"safety":"Read-only/non-destructive recommendations only."}
