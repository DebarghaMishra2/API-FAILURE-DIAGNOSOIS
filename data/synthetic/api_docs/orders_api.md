# Orders API Reference

Version: 3.2
Effective Date: 2026-02-01
Owner: Commerce API Team
Status: approved
Product: Acme Orders API
Environment: production

## GET /v1/orders/{order_id}
Returns a single order. The caller must have `orders:read` scope. A 404 indicates that the requested order does not exist in the selected tenant or that the route/resource identifier is incorrect.

## POST /v1/orders
Creates an order. Required JSON fields are `customer_id` (string), `items` (non-empty array), and `currency` (three-letter uppercase code). Unknown fields are rejected when strict schema validation is enabled. A 400 or 422 response indicates malformed JSON, a missing required field, an invalid field type or an unsupported enum value. The response may include a field-level validation path; redact customer values before sharing logs.

## Content type
Requests with JSON payloads must use `Content-Type: application/json`. Confirm the published schema for the deployed API version before changing a client request.
