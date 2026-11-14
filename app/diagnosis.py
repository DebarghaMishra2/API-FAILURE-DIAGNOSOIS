"""Evidence-weighted diagnosis ranking. Scores are heuristics, not probabilities."""
from __future__ import annotations
from .normalization import parse_datetime

CAUSE_LABELS={
 "authentication":"Authentication failure / invalid or expired credential",
 "authorization":"Authorization failure / missing role or scope",
 "validation":"Request validation or schema mismatch",
 "rate_limiting":"Rate limit or quota exhaustion",
 "timeout":"Request or upstream timeout",
 "dependency_error":"Upstream dependency or gateway failure",
 "server_error":"Application/server-side failure",
 "not_found":"Endpoint or resource not found",
 "unknown":"Insufficient evidence to classify the failure",
}
INFO_REQUIRED={
 "authentication":["Confirm token issuer, audience and expiry using approved identity-provider diagnostics; do not paste token values.","Check whether the request used the expected authentication scheme and key identifier."],
 "authorization":["Confirm the principal's required role and scopes with the API owner.","Check the resource-level permission policy and tenant/environment context."],
 "validation":["Compare sanitized field names and data types with the documented request schema.","Confirm required fields, allowed enum values and API version."],
 "rate_limiting":["Inspect sanitized rate-limit headers, quota window and Retry-After value.","Confirm the applicable tenant, endpoint and plan-level quota."],
 "timeout":["Inspect distributed trace spans and connect/read timeout boundaries.","Compare endpoint and downstream dependency latency for the same time window."],
 "dependency_error":["Check the dependency health dashboard and upstream trace/span for the same correlation ID.","Confirm whether the failure is isolated to one upstream dependency or multiple endpoints."],
 "server_error":["Inspect server-side exception logs using the redacted correlation ID.","Check deployment/change events and endpoint error-rate trends for the same period."],
 "not_found":["Confirm the HTTP method, base URL, API version and route template.","Check whether the resource identifier exists in the intended tenant/environment."],
 "unknown":["Provide a sanitized request/response log with timestamp, method, endpoint and status code.","Provide endpoint metrics and the relevant API documentation/error definition."],
}

def _f(v):
    try:return float(v)
    except (TypeError,ValueError):return None

def rank_diagnoses(classification, request, metric_corr, doc_results, error_text=""):
    primary=classification.get("category","unknown")
    scores={k:0.08 for k in CAUSE_LABELS if k!="unknown"}
    evidence={k:[] for k in scores}; contradictions={k:[] for k in scores}
    if primary in scores:
        scores[primary]+=0.55
        evidence[primary].append({"type":"request_response","summary":f"Observed HTTP status {classification.get('status_code')} and classifier signal: {' '.join(classification.get('reasons',[]))}","source":"request/response log"})
    status=classification.get("status_code")
    headers={str(k).lower():str(v) for k,v in {**(request.get("safe_request_headers") or {}),**(request.get("safe_response_headers") or {})}.items()}
    # Use header names/values only after redaction; rate-limit headers are safe metadata.
    if status==429:
        scores["rate_limiting"]+=0.20
        evidence["rate_limiting"].append({"type":"http_status","summary":"HTTP 429 is the standard too-many-requests signal.","source":"response status"})
    if status==401: scores["authentication"]+=0.10
    if status==403: scores["authorization"]+=0.10
    if status in (408,504): scores["timeout"]+=0.15
    if status in (502,503): scores["dependency_error"]+=0.15
    metrics=metric_corr.get("signals",{}) if metric_corr.get("matched") else {}
    p95=_f(metrics.get("p95_latency_ms")); base=_f(metrics.get("baseline_p95_latency_ms")); err=_f(metrics.get("error_rate_pct")); dep_err=_f(metrics.get("dependency_error_rate_pct")); dep_p95=_f(metrics.get("dependency_p95_latency_ms")); rps=_f(metrics.get("request_rate_rps")); base_rps=_f(metrics.get("baseline_request_rate_rps"))
    if metric_corr.get("matched"):
        evidence[primary if primary in evidence else "server_error"].append({"type":"metrics_correlation","summary":f"Metrics correlated to {metric_corr.get('endpoint')} ({metric_corr.get('time_match')}).","source":"endpoint metrics"})
    if p95 is not None and (p95>=1000 or (base and p95>=1.8*base)):
        scores["timeout"]+=0.20; evidence["timeout"].append({"type":"metric_anomaly","summary":f"Endpoint p95 latency is {p95:g} ms (baseline {base if base is not None else 'not available'} ms).","source":"endpoint metrics"})
    if err is not None and err>=5:
        scores["server_error"]+=0.10; scores["dependency_error"]+=0.05
        evidence["server_error"].append({"type":"metric_anomaly","summary":f"Endpoint error rate is {err:g}% (>=5% signal threshold).","source":"endpoint metrics"})
    if dep_err is not None and dep_err>0:
        scores["dependency_error"]+=0.25; evidence["dependency_error"].append({"type":"metric_anomaly","summary":f"Dependency error rate is {dep_err:g}%. ","source":"endpoint metrics"})
    if dep_p95 is not None and dep_p95>=1000:
        scores["dependency_error"]+=0.10; scores["timeout"]+=0.10
        evidence["dependency_error"].append({"type":"metric_anomaly","summary":f"Dependency p95 latency is {dep_p95:g} ms.","source":"endpoint metrics"})
    if status==429 and rps is not None and base_rps and rps>=1.8*base_rps:
        scores["rate_limiting"]+=0.15; evidence["rate_limiting"].append({"type":"traffic_spike","summary":f"Request rate {rps:g} rps is at least 1.8× baseline {base_rps:g} rps.","source":"endpoint metrics"})
    if any(k in headers for k in ("retry-after","x-ratelimit-remaining","ratelimit-remaining")):
        val=headers.get("x-ratelimit-remaining",headers.get("ratelimit-remaining",""))
        if status==429 and val.strip() in {"0","0.0"}:
            scores["rate_limiting"]+=0.15; evidence["rate_limiting"].append({"type":"response_header","summary":"A rate-limit remaining header indicates zero remaining quota.","source":"response headers"})
    for doc in doc_results:
        text=(str(doc.get("title",""))+" "+str(doc.get("section",""))+" "+str(doc.get("text",""))).lower()
        for cat,terms in {
          "authentication":["401","bearer","token","authentication"],"authorization":["403","scope","permission","role"],
          "validation":["400","422","schema","required field","validation"],"rate_limiting":["429","rate limit","quota","retry-after"],
          "timeout":["timeout","504","latency","deadline"],"dependency_error":["upstream","dependency","502","503","gateway"],
          "server_error":["500","internal server","server error"],"not_found":["404","route not found","resource not found"]}.items():
            hits=sum(1 for term in terms if term in text)
            if hits and cat in scores:
                scores[cat]+=min(0.10,0.025*hits)
                evidence[cat].append({"type":"documentation","summary":f"Relevant documentation passage: {doc.get('title')} — {doc.get('section')}.","source":doc.get("source")})
    if metric_corr.get("matched"):
        for msg in metric_corr.get("contradictions",[]):
            contradictions["timeout"].append({"type":"contradictory_metric","summary":msg,"source":"endpoint metrics"})
            contradictions["dependency_error"].append({"type":"contradictory_metric","summary":msg,"source":"endpoint metrics"})
    # Prevent a single status code from masquerading as confirmed root cause.
    ranked=[]
    for cat,score in scores.items():
        score=max(0.0,min(0.98,score))
        if score<0.18 and cat not in {primary}: continue
        confidence="high" if score>=0.78 and evidence[cat] else "medium" if score>=0.48 else "low"
        ranked.append({"cause":cat,"label":CAUSE_LABELS[cat],"score":round(score,3),"confidence":confidence,"supporting_evidence":evidence[cat],"contradictory_evidence":contradictions[cat],"information_still_required":INFO_REQUIRED[cat]})
    ranked.sort(key=lambda x:x["score"],reverse=True)
    if not ranked: ranked=[{"cause":"unknown","label":CAUSE_LABELS["unknown"],"score":0.0,"confidence":"low","supporting_evidence":[],"contradictory_evidence":[],"information_still_required":INFO_REQUIRED["unknown"]}]
    # Explain uncertainty explicitly; heuristic scores are ranking aids, not probabilities.
    for item in ranked: item["score_interpretation"]="Heuristic ranking score; not a calibrated probability or proof of root cause."
    return ranked[:5]
