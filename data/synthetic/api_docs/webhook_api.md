# Webhook Delivery Troubleshooting

Version: 1.0
Effective Date: 2026-04-20
Owner: Integrations Team
Status: approved
Product: Acme Webhooks

## Delivery failures
Webhook delivery attempts are recorded with an event identifier and attempt timestamp. A destination timeout should be investigated using the destination's response latency and the delivery trace. An HTTP 4xx from the destination generally requires reviewing the destination endpoint contract; an HTTP 5xx may be transient but must not trigger uncontrolled retry loops.

## Safe checks
Confirm the configured destination URL and supported method without exposing query-string secrets. Inspect sanitized response status and retry metadata. Escalate certificate, DNS and destination permission changes to the service owner.
