"""End-to-end API failure diagnosis orchestration."""
from __future__ import annotations
from datetime import datetime, timezone
from .classification import classify_failure
from .request_analysis import analyze_request
from .metrics import correlate_metrics
from .retrieval import DocumentationRetriever
from .diagnosis import rank_diagnoses
from .guidance import diagnostic_guidance
from .reporting import build_report
from .llm import generate_explanation
from .normalization import new_case_id, parse_datetime
from .redaction import redact_structure, redact_text

def _select_event(logs):
    if not logs: return {}
    def key(x): return parse_datetime(x.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc)
    return sorted(logs,key=key)[-1]

def analyze_case(case: dict, logs=None, metrics=None, error_text="", documents=None, use_groq=True) -> dict:
    logs=list(logs if logs is not None else case.get("logs",[]))
    metrics=list(metrics if metrics is not None else case.get("metrics",[]))
    documents=list(documents if documents is not None else case.get("documents",[]))
    event=_select_event(logs) if logs else dict(case.get("event",{}))
    if not event and case.get("request"):
        event={**case.get("request",{}),**case.get("response",{})}
    event=redact_structure(event)
    error_text=redact_text(error_text or case.get("error_message","") or event.get("error_message", ""))
    classification=classify_failure(event,error_text)
    request=analyze_request(event)
    metric_corr=correlate_metrics(request.get("endpoint","/"),request.get("timestamp"),metrics,int(case.get("correlation_window_seconds",300)))
    query=" ".join([str(classification.get("category")),str(request.get("method")),str(request.get("endpoint")),str(request.get("status_code")),error_text,str(request.get("error_message"))])
    if case.get("documentation_available") is False: documents=[]
    chunks=[]
    for doc in documents:
        chunks.extend(doc.get("chunks",[]))
    retriever=DocumentationRetriever(chunks)
    docs=retriever.search(query,top_k=5)
    ranked=rank_diagnoses(classification,request,metric_corr,docs,error_text)
    primary=classification.get("category","unknown")
    guidance=diagnostic_guidance(primary)
    uncertainty=[]
    if primary=="unknown": uncertainty.append("Failure class is unknown because request/response evidence is incomplete.")
    if not metric_corr.get("matched"): uncertainty.append(metric_corr.get("reason","Endpoint metrics were not supplied."))
    if not docs: uncertainty.append("No API documentation passages were supplied or retrieved.")
    if not request.get("timestamp"): uncertainty.append("Request timestamp is missing; time-window metric correlation cannot be verified.")
    if not request.get("correlation_id"): uncertainty.append("No usable correlation identifier was supplied (or it was redacted); trace-level correlation may be limited.")
    if primary in {"server_error","dependency_error","timeout"}: uncertainty.append("A status/error signal suggests an infrastructure or server issue, but root cause requires trace or service-owner confirmation.")
    base={"classification":classification,"request_analysis":request,"metric_correlation":metric_corr,"documentation_evidence":docs,"ranked_diagnoses":ranked,"diagnostic_guidance":guidance,"uncertainty":uncertainty}
    summary=generate_explanation(base) if use_groq else {"text":None,"mode":"disabled","reason":"Groq narrative disabled for this run."}
    report=build_report(case.get("case_id") or new_case_id(),classification,request,metric_corr,docs,ranked,guidance,summary,uncertainty)
    report["case_title"]=redact_text(case.get("title","API Failure Case"))
    report["case_description"]=redact_text(case.get("description",""))
    report["input_counts"]={"log_records":len(logs),"metric_records":len(metrics),"documents":len(documents),"documentation_chunks":len(chunks)}
    return report
