"""HTTP request/response analysis with redaction-safe summaries."""
from __future__ import annotations
import json
from urllib.parse import urlsplit
from .normalization import normalize_method, safe_endpoint, safe_id
from .redaction import redact_structure, redact_text

def _to_int(value):
    try: return int(float(value))
    except (TypeError,ValueError): return None

def _to_float(value):
    try: return float(value)
    except (TypeError,ValueError): return None

def _headers_dict(value):
    if isinstance(value,dict): return value
    if isinstance(value,str):
        try:
            parsed=json.loads(value)
            return parsed if isinstance(parsed,dict) else {}
        except Exception: return {}
    return {}

def analyze_request(event: dict) -> dict:
    event=redact_structure(event or {})
    method=normalize_method(event.get("method"))
    endpoint=safe_endpoint(str(event.get("endpoint") or "/"))
    request_headers=_headers_dict(event.get("request_headers") or event.get("headers"))
    response_headers=_headers_dict(event.get("response_headers"))
    lower_req={str(k).lower():v for k,v in request_headers.items()}
    lower_resp={str(k).lower():v for k,v in response_headers.items()}
    safe_names={"content-type","accept","user-agent","x-api-version"}
    safe_header_values={k:redact_text(str(v))[:120] for k,v in lower_req.items() if k in safe_names}
    safe_response_names={"content-type","retry-after","x-ratelimit-limit","x-ratelimit-remaining","x-ratelimit-reset","ratelimit-limit","ratelimit-remaining","ratelimit-reset"}
    safe_response_values={k:redact_text(str(v))[:120] for k,v in lower_resp.items() if k in safe_response_names}
    payload=event.get("request_payload")
    if payload is None: payload=event.get("request_body")
    if isinstance(payload,str):
        try: payload_obj=json.loads(payload)
        except Exception: payload_obj=None
        size=len(payload.encode("utf-8"))
    elif payload is not None:
        payload_obj=payload; size=len(json.dumps(payload,default=str).encode("utf-8"))
    else: payload_obj=None; size=0
    def keys_of(obj,prefix=""):
        keys=[]
        if isinstance(obj,dict):
            for k,v in obj.items():
                if any(s in str(k).lower() for s in ("password","token","secret","key","credential")): continue
                full=f"{prefix}.{k}" if prefix else str(k)
                keys.append(full)
                if isinstance(v,dict): keys.extend(keys_of(v,full))
        return keys[:40]
    query_keys=[]
    raw_endpoint=str(event.get("endpoint") or event.get("url") or "")
    try: query_keys=[x.split("=",1)[0][:60] for x in urlsplit(raw_endpoint).query.split("&") if x]
    except Exception: pass
    status=_to_int(event.get("status_code"))
    latency=_to_float(event.get("latency_ms"))
    return {
        "method":method,"endpoint":endpoint,"status_code":status,"latency_ms":latency,
        "timestamp":event.get("timestamp"),"correlation_id":safe_id(event.get("correlation_id")),"source_file":event.get("source_file"),
        "request_header_names":sorted(str(k).lower() for k in request_headers.keys()),
        "response_header_names":sorted(str(k).lower() for k in response_headers.keys()),
        "safe_request_headers":safe_header_values,"safe_response_headers":safe_response_values,
        "has_authorization_header":"authorization" in lower_req,
        "has_cookie_header":"cookie" in lower_req,
        "response_content_type":redact_text(str(lower_resp.get("content-type","")))[:120],
        "payload_size_bytes":size,"payload_field_names":keys_of(payload_obj),
        "query_parameter_names":query_keys,
        "error_message":redact_text(str(event.get("error_message") or event.get("response_message") or ""))[:1000],
    }
