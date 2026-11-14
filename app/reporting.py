"""Audit-friendly JSON and Markdown report serializers."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from .redaction import redact_structure

def build_report(case_id,classification,request_analysis,metric_correlation,documentation_evidence,ranked_diagnoses,guidance,summary=None,uncertainty=None):
    report={"report_id":case_id,"generated_at":datetime.now(timezone.utc).isoformat(),"classification":classification,"request_analysis":request_analysis,"metric_correlation":metric_correlation,"documentation_evidence":documentation_evidence,"ranked_diagnoses":ranked_diagnoses,"diagnostic_guidance":guidance,"summary":summary or {},"uncertainty":uncertainty or [],"root_cause_confirmed":False,"notice":"Probable causes are ranked hypotheses unless the supplied evidence establishes a confirmed root cause."}
    return redact_structure(report)

def to_json(report): return json.dumps(redact_structure(report),indent=2,ensure_ascii=False,default=str)

def to_markdown(report):
    c=report.get("classification",{}); req=report.get("request_analysis",{}); metrics=report.get("metric_correlation",{})
    lines=[f"# API Failure Diagnosis Report — {report.get('report_id')}","",f"Generated: {report.get('generated_at')}","","> Probable causes are hypotheses; root cause is not marked confirmed unless evidence establishes it.","","## Failure classification",f"- Category: **{c.get('category','unknown')}**",f"- HTTP status: `{c.get('status_code')}`",* [f"- {x}" for x in c.get("reasons",[])],"","## Request analysis",f"- Method/endpoint: `{req.get('method')} {req.get('endpoint')}`",f"- Status: `{req.get('status_code')}`",f"- Latency: `{req.get('latency_ms')} ms`",f"- Correlation ID: `{req.get('correlation_id')}`",f"- Log source: `{req.get('source_file') or 'synthetic scenario / not provided'}`",f"- Request header names: {', '.join(req.get('request_header_names',[]))}",f"- Payload fields (names only): {', '.join(req.get('payload_field_names',[]))}","","## Metric correlation"]
    if metrics.get("matched"):
        lines += [f"- Matched endpoint: `{metrics.get('endpoint')}`",f"- Time match: `{metrics.get('time_match')}`",f"- Signals: `{json.dumps(metrics.get('signals',{}),default=str)}`"]
        lines += [f"- Anomaly: {x}" for x in metrics.get("anomalies",[])]
        lines += [f"- Contradiction: {x}" for x in metrics.get("contradictions",[])]
    else: lines.append(f"- Not correlated: {metrics.get('reason')}")
    lines += ["","## Ranked diagnosis hypotheses"]
    for i,d in enumerate(report.get("ranked_diagnoses",[]),1):
        lines += [f"### {i}. {d.get('label')} — {d.get('confidence')} confidence (heuristic score {d.get('score')})", "", "Supporting evidence:"]
        lines += [f"- {e.get('summary')} (source: {e.get('source')})" for e in d.get("supporting_evidence",[])] or ["- No direct supporting item attached."]
        lines += ["Contradictory evidence:"]
        lines += [f"- {e.get('summary')} (source: {e.get('source')})" for e in d.get("contradictory_evidence",[])] or ["- None observed in supplied evidence."]
        lines += ["Information still required:"]+[f"- {x}" for x in d.get("information_still_required",[])]
    lines += ["","## API documentation evidence"]
    for d in report.get("documentation_evidence",[]): lines.append(f"- **{d.get('title')} / {d.get('section')}** ({d.get('source')}, score {d.get('retrieval_score')}): {d.get('text','')[:600]}")
    lines += ["","## Safe verification guidance"]+[f"- {x}" for x in report.get("diagnostic_guidance",{}).get("verification_steps",[])]
    lines += ["",report.get("diagnostic_guidance",{}).get("escalation","")]
    if report.get("summary",{}).get("text"): lines += ["","## Narrative summary",report["summary"]["text"]]
    if report.get("uncertainty"): lines += ["","## Uncertainty"]+[f"- {x}" for x in report["uncertainty"]]
    return "\n".join(lines)+"\n"
