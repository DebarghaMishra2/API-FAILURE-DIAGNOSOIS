"""Optional Groq narrative helper; deterministic diagnosis remains the source of truth."""
from __future__ import annotations
import os, requests

GROQ_URL="https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL="openai/gpt-oss-20b"

def generate_explanation(report: dict, timeout: int=25) -> dict:
    key=os.getenv("GROQ_API_KEY","").strip()
    if not key: return {"text":None,"mode":"template_fallback","reason":"GROQ_API_KEY is not configured; deterministic diagnosis is still available."}
    model=os.getenv("GROQ_MODEL",DEFAULT_MODEL).strip() or DEFAULT_MODEL
    payload={
      "model":model,"temperature":0.1,"max_tokens":500,
      "messages":[
        {"role":"system","content":"You are an API reliability analyst. Summarize only the structured evidence supplied. Do not invent a root cause, credentials, metrics, or documentation facts. Clearly distinguish likely cause from confirmed root cause. Mention contradictions and missing information. Recommend only safe read-only checks. Return plain concise prose."},
        {"role":"user","content":str({"classification":report.get("classification"),"request_analysis":report.get("request_analysis"),"metric_correlation":report.get("metric_correlation"),"ranked_diagnoses":report.get("ranked_diagnoses"),"documentation_evidence":report.get("documentation_evidence"),"uncertainty":report.get("uncertainty")})[:12000]}
      ]}
    try:
        response=requests.post(GROQ_URL,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json=payload,timeout=timeout)
        response.raise_for_status()
        content=response.json()["choices"][0]["message"].get("content","").strip()
        if not content: raise ValueError("Groq returned an empty response")
        return {"text":content,"mode":model,"reason":None}
    except Exception as exc:
        # Do not leak request headers or secrets in exception messages.
        return {"text":None,"mode":"template_fallback","reason":f"Optional Groq summary unavailable ({type(exc).__name__}); deterministic findings remain authoritative."}
