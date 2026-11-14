"""Rule-based API failure classification with explicit reasons."""
from __future__ import annotations
import re

CATEGORIES=["authentication","authorization","validation","rate_limiting","timeout","dependency_error","server_error","not_found"]

def classify_failure(event: dict, error_text: str="") -> dict:
    status=event.get("status_code")
    try: status=int(status) if status not in (None,"") else None
    except (ValueError,TypeError): status=None
    text=" ".join([str(error_text or ""),str(event.get("error_message") or ""),str(event.get("response_message") or "")]).lower()
    reasons=[]; alternatives=[]; category="unknown"
    if status==401 or re.search(r"invalid token|expired token|missing (?:api )?key|authentication required|unauthenticated|invalid api key",text):
        category="authentication"; reasons.append("HTTP 401 or an explicit authentication/token failure was observed.")
    elif status==403 or re.search(r"forbidden|insufficient scope|permission denied|not authorized|access denied",text):
        category="authorization"; reasons.append("HTTP 403 or an explicit permission/scope failure was observed.")
    elif status==429 or re.search(r"rate.?limit|quota exceeded|too many requests|throttl",text):
        category="rate_limiting"; reasons.append("HTTP 429 or an explicit rate-limit/quota signal was observed.")
    elif status in (408,504) or re.search(r"timed? ?out|timeout|deadline exceeded|read timeout|connect timeout",text):
        category="timeout"; reasons.append("A timeout status or timeout-related error message was observed.")
    elif status in (502,503) or re.search(r"upstream|connection refused|connection reset|service unavailable|dependency unavailable|dns resolution",text):
        category="dependency_error"; reasons.append("A gateway/dependency status or an upstream connectivity error was observed.")
    elif status in (400,409,422) or re.search(r"validation error|invalid parameter|malformed request|schema mismatch|missing required field|invalid field",text):
        category="validation"; reasons.append("A 4xx validation status or a request/schema validation message was observed.")
    elif status==404 or re.search(r"route not found|endpoint not found|resource not found",text):
        category="not_found"; reasons.append("The endpoint or requested resource appears not to exist.")
    elif status is not None and 500<=status<=599:
        category="server_error"; reasons.append("An HTTP 5xx response indicates a server-side failure; supplied evidence does not yet isolate the failing component.")
    elif status is not None and 400<=status<=499:
        category="validation"; reasons.append("A client-side 4xx response was observed; inspect request and endpoint requirements.")
    elif not status and text:
        if re.search(r"ssl|tls|dns|connection refused|upstream",text): category="dependency_error"
        elif re.search(r"timeout|timed out",text): category="timeout"
        else: category="unknown"
        if category!="unknown": reasons.append("The error text contains a matching infrastructure failure signal.")
    if category=="unknown": reasons.append("No supplied status code or error text uniquely identifies a failure class.")
    if category in {"server_error","dependency_error"}: alternatives=["dependency_error","server_error","timeout"]
    elif category=="authentication": alternatives=["authorization","validation"]
    elif category=="authorization": alternatives=["authentication","validation"]
    elif category=="validation": alternatives=["not_found","authorization"]
    elif category=="rate_limiting": alternatives=["dependency_error","server_error"]
    elif category=="timeout": alternatives=["dependency_error","server_error"]
    elif category=="not_found": alternatives=["validation","authorization"]
    else: alternatives=["server_error","dependency_error"]
    return {"category":category,"status_code":status,"reasons":reasons,"alternative_categories":alternatives}
