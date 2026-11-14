"""Endpoint/time metric correlation and anomaly feature extraction."""
from __future__ import annotations
from statistics import median
from .normalization import normalize_endpoint, parse_datetime

def _num(v):
    try: return float(v)
    except (TypeError,ValueError): return None

def correlate_metrics(endpoint: str, timestamp, metrics: list[dict], window_seconds: int=300) -> dict:
    target=normalize_endpoint(endpoint)
    target_dt=parse_datetime(timestamp)
    same=[m for m in metrics if normalize_endpoint(str(m.get("endpoint") or m.get("path") or "/"))==target]
    if not same:
        return {"matched":False,"reason":"No metrics for the same normalized endpoint were supplied.","endpoint":target,"signals":{},"contradictions":[]}
    candidates=[]
    for m in same:
        mdt=parse_datetime(m.get("timestamp"))
        if target_dt and mdt:
            diff=abs((mdt-target_dt).total_seconds())
            if diff<=window_seconds: candidates.append((diff,m))
        elif not target_dt or not mdt:
            candidates.append((float("inf"),m))
    if not candidates:
        return {"matched":False,"reason":f"Metrics exist for this endpoint but none fall within ±{window_seconds} seconds of the event.","endpoint":target,"signals":{},"contradictions":[]}
    candidates.sort(key=lambda x:x[0]); selected=candidates[0][1]; diff=candidates[0][0]
    p95=_num(selected.get("p95_latency_ms") or selected.get("latency_p95_ms"))
    err=_num(selected.get("error_rate_pct") or selected.get("error_rate"))
    rps=_num(selected.get("request_rate_rps") or selected.get("rps"))
    dep_err=_num(selected.get("dependency_error_rate_pct") or selected.get("dependency_errors"))
    dep_p95=_num(selected.get("dependency_p95_latency_ms"))
    baseline_rows=[m for m in same if m is not selected]
    baseline_p95=[_num(m.get("p95_latency_ms") or m.get("latency_p95_ms")) for m in baseline_rows]
    baseline_p95=[x for x in baseline_p95 if x is not None]
    baseline_rps=[_num(m.get("request_rate_rps") or m.get("rps")) for m in baseline_rows]
    baseline_rps=[x for x in baseline_rps if x is not None]
    med_p95=median(baseline_p95) if baseline_p95 else None
    med_rps=median(baseline_rps) if baseline_rps else None
    signals={"p95_latency_ms":p95,"error_rate_pct":err,"request_rate_rps":rps,"dependency_error_rate_pct":dep_err,"dependency_p95_latency_ms":dep_p95,"baseline_p95_latency_ms":med_p95,"baseline_request_rate_rps":med_rps}
    # Include only approved, non-payload metric fields in the audit result.
    safe_selected={"source_file":selected.get("source_file"),"timestamp":selected.get("timestamp"),"endpoint":target,"p95_latency_ms":p95,"error_rate_pct":err,"request_rate_rps":rps,"dependency_error_rate_pct":dep_err,"dependency_p95_latency_ms":dep_p95}
    anomalies=[]; contradictions=[]
    if p95 is not None and p95>=1000: anomalies.append("Endpoint p95 latency is at least 1000 ms.")
    if p95 is not None and med_p95 and p95>=1.8*med_p95: anomalies.append("Endpoint p95 latency is at least 1.8× its same-endpoint baseline.")
    if err is not None and err>=5: anomalies.append("Endpoint error rate is at least 5%.")
    if dep_err is not None and dep_err>0: anomalies.append("Dependency error rate is non-zero.")
    if dep_p95 is not None and dep_p95>=1000: anomalies.append("Dependency p95 latency is at least 1000 ms.")
    if rps is not None and med_rps and rps>=1.8*med_rps: anomalies.append("Request rate is at least 1.8× its same-endpoint baseline.")
    if p95 is not None and p95<500 and (err is None or err<1): contradictions.append("Correlated endpoint metrics show low latency and low error rate; this weakens a broad endpoint-outage hypothesis but does not disprove an individual request failure.")
    if dep_err==0 and (dep_p95 is None or dep_p95<500): contradictions.append("Correlated dependency metrics show no dependency errors and low dependency latency.")
    return {"matched":True,"endpoint":target,"timestamp_delta_seconds":None if diff==float("inf") else int(diff),"time_match":"within_window" if diff!=float("inf") else "time_unknown","window_seconds":window_seconds,"selected_metric":safe_selected,"signals":signals,"anomalies":anomalies,"contradictions":contradictions,"baseline_samples":len(baseline_rows)}
