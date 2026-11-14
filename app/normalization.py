"""Normalization and safe parsing helpers."""
from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import urlsplit
import re
import uuid

def parse_datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt=value
    else:
        text=str(value).strip().replace("Z", "+00:00")
        try:
            dt=datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def normalize_endpoint(value: str) -> str:
    """Remove query strings and normalize numeric/UUID path segments for joins."""
    raw=str(value or "").strip()
    if not raw:
        return "/"
    parts=urlsplit(raw)
    path=parts.path if parts.scheme or parts.netloc else raw.split("?",1)[0]
    path=path or "/"
    path=re.sub(r"(?i)/[0-9a-f]{8}-[0-9a-f-]{27,}", "/{id}", path)
    path=re.sub(r"/\d+(?=/|$)", "/{id}", path)
    if not path.startswith("/"):
        path="/"+path
    return re.sub(r"/{2,}", "/", path).rstrip("/") or "/"

def safe_endpoint(value: str) -> str:
    """Return path only; strip query strings which may contain secrets or PII."""
    return normalize_endpoint(value)

def normalize_method(value: str) -> str:
    method=str(value or "UNKNOWN").upper().strip()
    return method if re.fullmatch(r"[A-Z]{3,12}", method) else "UNKNOWN"

def safe_id(value: str | None) -> str | None:
    if not value:
        return None
    text=str(value)
    return f"…{text[-4:]}" if len(text)>4 else "[REDACTED_ID]"

def new_case_id() -> str:
    return f"CASE-{uuid.uuid4().hex[:10].upper()}"
