"""Credential and sensitive-data redaction utilities."""
from __future__ import annotations
import re
from typing import Any

SENSITIVE_KEY_FRAGMENTS = (
    "authorization", "cookie", "set-cookie", "password", "passwd", "secret",
    "api_key", "apikey", "access_token", "refresh_token", "id_token",
    "client_secret", "private_key", "credential", "session_token", "bearer",
)

PATTERNS = [
    (re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|secret)\b\s*[:=]\s*)['\"]?[^\s,;\"']+"), r"\1[REDACTED]"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I), "Bearer [REDACTED]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"), "[REDACTED_JWT]"),
    (re.compile(r"\b(?:gsk_[A-Za-z0-9]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|sk-[A-Za-z0-9_-]{12,})\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"(?i)(cookie\s*[:=]\s*)[^\r\n]+"), r"\1[REDACTED]"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
]

def redact_text(value: Any) -> str:
    text = str(value if value is not None else "")
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text

def _is_sensitive_key(key: Any) -> bool:
    normalized = str(key).lower().replace("-", "_").replace(" ", "_")
    return any(fragment in normalized for fragment in SENSITIVE_KEY_FRAGMENTS)

def redact_structure(value: Any) -> Any:
    """Recursively redact sensitive fields and secret-like strings."""
    if isinstance(value, dict):
        return {str(k): ("[REDACTED]" if _is_sensitive_key(k) else redact_structure(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_structure(item) for item in value]
    if isinstance(value, tuple):
        return [redact_structure(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
