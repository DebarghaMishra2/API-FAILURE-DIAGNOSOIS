from __future__ import annotations
import os, sys, json
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
load_dotenv(ROOT/".env",override=False)
try:
    _secret=st.secrets.get("GROQ_API_KEY")
    if _secret: os.environ["GROQ_API_KEY"]=str(_secret)
    _model=st.secrets.get("GROQ_MODEL")
    if _model: os.environ["GROQ_MODEL"]=str(_model)
except Exception:
    pass

from app.synthetic import list_scenarios,load_scenario,load_synthetic_documents
from app.ingestion import parse_log_uploads,parse_metric_uploads,parse_error_uploads,parse_document_uploads
from app.engine import analyze_case
from app.normalization import safe_endpoint, safe_id
from app.reporting import to_json,to_markdown
from app.feedback import save_feedback,list_feedback

st.set_page_config(page_title="Intelligent API Failure Diagnosis",page_icon="🛠️",layout="wide")
st.title("🛠️ Intelligent API Failure Diagnosis Assistant")
st.caption("Evidence-backed API failure investigation · redacted request analysis · endpoint/time metric correlation · ranked hypotheses")

with st.sidebar:
    st.header("1. Choose evidence source")
    mode=st.radio("Analysis mode",["Synthetic demo case","Upload an incident"],index=0)
    st.divider()
    groq_key=bool(os.getenv("GROQ_API_KEY",""))
    if groq_key:
        st.success("Groq key detected — optional narrative enabled")
    else:
        st.info("Groq key not configured. Deterministic classification and diagnosis still work; narrative uses a template fallback.")
    st.caption("Groq summarizes the structured findings only. Rule-based classification and ranking remain authoritative.")

report=None
if mode=="Synthetic demo case":
    scenarios=list_scenarios()
    labels=[f"{x['case_id']} — {x['title']}" for x in scenarios]
    selected=st.selectbox("Synthetic incident",labels,index=0)
    case_id=scenarios[labels.index(selected)]["case_id"]
    case=load_scenario(case_id)
    documents=load_synthetic_documents()
    st.info("Synthetic data is fictional. It contains 8 scenarios (401, 403, 422, 429, 504, 503, 500 and an incomplete-evidence case) plus API documentation for deterministic testing.")
    with st.expander("Preview case details"):
        st.write(case.get("description"))
        ev=case.get("event",{})
        st.json({"request_summary":{"method":ev.get("method"),"endpoint":safe_endpoint(str(ev.get("endpoint") or "/")),"status_code":ev.get("status_code"),"latency_ms":ev.get("latency_ms"),"timestamp":ev.get("timestamp"),"correlation_id":safe_id(ev.get("correlation_id"))},"test_label_for_demo":case.get("expected_category")})
    run=st.button("Analyze synthetic failure",type="primary",use_container_width=False)
else:
    st.subheader("Upload incident evidence")
    log_files=st.file_uploader("Request/response logs (JSON, JSONL, CSV)",type=["json","jsonl","ndjson","csv"],accept_multiple_files=True,key="logs") or []
    metric_files=st.file_uploader("Endpoint metrics (CSV or JSON)",type=["csv","json","jsonl"],accept_multiple_files=True,key="metrics") or []
    error_files=st.file_uploader("Error messages / stack excerpts (TXT, JSON, JSONL, CSV)",type=["txt","json","jsonl","csv"],accept_multiple_files=True,key="errors") or []
    doc_files=st.file_uploader("API documentation (PDF, HTML, Markdown, TXT)",type=["pdf","html","htm","md","markdown","txt"],accept_multiple_files=True,key="docs") or []
    st.caption("Files are processed in memory for this session. Secrets and common personal identifiers are redacted before analysis and report generation. Do not upload raw production payloads unless authorized.")
    run=st.button("Analyze uploaded incident",type="primary")
    case={"case_id":"UPLOAD-INCIDENT","title":"Uploaded API incident","description":"User-supplied request, metric, error and documentation evidence."}
    documents=[]
    if run:
        try:
            logs=parse_log_uploads([(f.name,f.getvalue()) for f in log_files])
            metrics=parse_metric_uploads([(f.name,f.getvalue()) for f in metric_files])
            error_text=parse_error_uploads([(f.name,f.getvalue()) for f in error_files])
            documents=parse_document_uploads([(f.name,f.getvalue()) for f in doc_files])
            case["logs"]=logs
            if not logs and not error_text:
                st.error("Upload at least one structured request/response log or error message.")
                run=False
            else:
                case["case_id"]="UPLOAD-"+str(abs(hash((len(logs),len(metrics),len(documents),error_text[:100]))))[:10]
        except Exception as exc:
            st.error(f"Could not parse uploaded evidence: {type(exc).__name__}: {exc}")
            run=False

if run:
    try:
        if mode=="Upload an incident":
            # Parse again only once in the submit branch; local variables above are scoped to this script run.
            logs=parse_log_uploads([(f.name,f.getvalue()) for f in log_files])
            metrics=parse_metric_uploads([(f.name,f.getvalue()) for f in metric_files])
            error_text=parse_error_uploads([(f.name,f.getvalue()) for f in error_files])
            documents=parse_document_uploads([(f.name,f.getvalue()) for f in doc_files])
            case["logs"]=logs
            report=analyze_case(case,logs=logs,metrics=metrics,error_text=error_text,documents=documents,use_groq=True)
        else:
            report=analyze_case(case,documents=documents,use_groq=True)
        st.session_state["latest_report"]=report
        st.session_state["latest_report_mode"]=mode
    except Exception as exc:
        st.exception(exc)
        st.stop()

report=st.session_state.get("latest_report")
if report:
    st.divider()
    st.subheader("2. Failure classification and request analysis")
    cls=report.get("classification",{}); req=report.get("request_analysis",{})
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Failure category",cls.get("category","unknown").replace("_"," ").title())
    c2.metric("HTTP status",str(cls.get("status_code") or "Unknown"))
    c3.metric("Latency",f"{req.get('latency_ms')} ms" if req.get("latency_ms") is not None else "Unknown")
    c4.metric("Documentation passages",report.get("input_counts",{}).get("documentation_chunks",0))
    st.write("**Classifier signals**")
    for reason in cls.get("reasons",[]): st.write("• "+reason)
    with st.expander("Redacted request metadata",expanded=True):
        safe={k:req.get(k) for k in ["method","endpoint","status_code","latency_ms","timestamp","correlation_id","source_file","request_header_names","response_header_names","safe_request_headers","has_authorization_header","has_cookie_header","response_content_type","payload_size_bytes","payload_field_names","query_parameter_names","error_message"]}
        st.json(safe)
        st.caption("Header names and selected safe metadata are shown; authorization/cookie values and payload values are never rendered.")

    st.subheader("3. Correlated endpoint metrics")
    corr=report.get("metric_correlation",{})
    if corr.get("matched"):
        st.success(f"Matched same normalized endpoint; time match: {corr.get('time_match')} (window ±{corr.get('window_seconds')} seconds).")
        signals=corr.get("signals",{})
        metric_cols=st.columns(4)
        for col,(key,label,suffix) in zip(metric_cols,[("p95_latency_ms","Endpoint p95"," ms"),("error_rate_pct","Error rate","%"),("request_rate_rps","Traffic"," rps"),("dependency_error_rate_pct","Dependency errors","%")]):
            val=signals.get(key); col.metric(label,f"{val}{suffix}" if val is not None else "Not supplied")
        for text in corr.get("anomalies",[]): st.warning(text)
        for text in corr.get("contradictions",[]): st.info("Counter-evidence: "+text)
        with st.expander("Metric correlation details"): st.json(corr)
    else:
        st.warning(corr.get("reason","No endpoint metrics were correlated."))

    st.subheader("4. Ranked diagnosis hypotheses")
    st.caption("Scores are heuristic ranking scores, not probabilities. Probable causes are not confirmed root causes.")
    for idx,item in enumerate(report.get("ranked_diagnoses",[]),1):
        with st.expander(f"#{idx} {item.get('label')} · {item.get('confidence')} confidence · score {item.get('score')}",expanded=(idx==1)):
            left,right=st.columns(2)
            with left:
                st.markdown("**Supporting evidence**")
                if item.get("supporting_evidence"):
                    for ev in item["supporting_evidence"]: st.write(f"• {ev.get('summary')} _(source: {ev.get('source')})_")
                else: st.write("No direct supporting evidence attached.")
            with right:
                st.markdown("**Contradictory / counter-evidence**")
                if item.get("contradictory_evidence"):
                    for ev in item["contradictory_evidence"]: st.write(f"• {ev.get('summary')} _(source: {ev.get('source')})_")
                else: st.write("No contradictory evidence found in supplied data.")
            st.markdown("**Information still required**")
            for q in item.get("information_still_required",[]): st.write("• "+q)

    st.subheader("5. API documentation evidence")
    docs=report.get("documentation_evidence",[])
    if docs:
        for i,d in enumerate(docs,1):
            with st.expander(f"[D{i}] {d.get('title')} · {d.get('section')} · score {d.get('retrieval_score')}"):
                st.caption(f"Source: {d.get('source')} · Version: {d.get('metadata',{}).get('version','not stated')} · Page: {d.get('page') or 'not available'}")
                st.write(d.get("text"))
    else: st.info("No API documentation evidence was retrieved. Diagnosis remains based on logs and metrics only.")

    st.subheader("6. Safe diagnostic guidance")
    guidance=report.get("diagnostic_guidance",{})
    for i,step in enumerate(guidance.get("verification_steps",[]),1): st.write(f"{i}. {step}")
    st.warning(guidance.get("escalation",""))
    st.caption("No production changes, credential operations, service restarts or automated recovery are performed.")

    st.subheader("7. Diagnosis summary")
    summary=report.get("summary",{})
    if summary.get("text"): st.write(summary["text"])
    else: st.info("Deterministic diagnosis is available. Optional Groq narrative is not configured or could not be reached: "+str(summary.get("reason")))
    if report.get("uncertainty"):
        st.markdown("**Uncertainty / missing evidence**")
        for item in report["uncertainty"]: st.write("• "+item)

    st.subheader("8. Audit report and reviewer feedback")
    col1,col2=st.columns(2)
    col1.download_button("Download JSON report",data=to_json(report),file_name=f"{report['report_id']}.json",mime="application/json",use_container_width=True)
    col2.download_button("Download Markdown report",data=to_markdown(report),file_name=f"{report['report_id']}.md",mime="text/markdown",use_container_width=True)
    with st.form("review_feedback"):
        st.markdown("**Reviewer decision on the top-ranked diagnosis**")
        decision=st.radio("Decision",["confirmed","rejected","annotated"],horizontal=True)
        reviewer=st.text_input("Reviewer identifier (optional)",value="reviewer")
        annotation=st.text_area("Annotation / reason (optional)",max_chars=2000)
        submitted=st.form_submit_button("Save reviewer feedback")
        if submitted:
            try:
                save_feedback(report["report_id"],decision,annotation,reviewer,report.get("ranked_diagnoses",[{}])[0])
                st.success("Reviewer feedback saved to the local SQLite feedback store.")
            except Exception as exc: st.error(f"Feedback could not be saved: {exc}")
    feedback=list_feedback()
    if feedback:
        with st.expander(f"Reviewer feedback history ({len(feedback)})"):
            st.dataframe(pd.DataFrame([{k:v for k,v in row.items() if k!="diagnosis_json"} for row in feedback]),use_container_width=True)
            st.download_button("Download feedback CSV",data=pd.DataFrame([{k:v for k,v in row.items() if k!="diagnosis_json"} for row in feedback]).to_csv(index=False),file_name="reviewer_feedback.csv",mime="text/csv")
else:
    st.info("Choose a synthetic incident or upload evidence, then click Analyze. The included demo cases cover the required 4xx, 5xx, authentication, timeout and rate-limit scenarios.")

with st.expander("Scope and safety boundaries"):
    st.write("This assistant investigates supplied evidence and recommends safe verification steps. It does not call the diagnosed API, execute recovery, change permissions, rotate credentials, raise quotas, restart services or modify production configuration. A likely cause is not a confirmed root cause unless evidence establishes it.")
