# Authentication and Authorization Requirements

Document Version: 1.4
Effective Date: 2026-01-15
Document Owner: Platform Identity Team
Status: approved
Product: Acme Public API
Environment: all

## Authentication
All API requests must use the Bearer authentication scheme over HTTPS. A 401 response indicates that authentication is missing, invalid, expired, or not accepted by the token issuer. The client should verify token issuer, audience, expiry and the configured authentication scheme using approved identity-provider diagnostics. Never log or share raw token values.

## Authorization
A 403 response indicates that the authenticated principal is not permitted to perform the requested operation. The Orders API read endpoint requires the `orders:read` scope. A valid token without the required scope can still receive 403. Role or scope changes require an authorized administrator and must follow change control.
