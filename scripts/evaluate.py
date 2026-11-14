from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.synthetic import list_scenarios,load_synthetic_documents
from app.engine import analyze_case
from collections import Counter

def main():
    docs=load_synthetic_documents(); cases=list_scenarios(); correct=0; top1=0; top3=0; details=[]
    for case in cases:
        report=analyze_case(case,documents=docs,use_groq=False)
        predicted=report["classification"]["category"]
        expected=case["expected_category"]
        ranked=[x["cause"] for x in report["ranked_diagnoses"]]
        c=predicted==expected; t1=bool(ranked and ranked[0]==case["expected_top_cause"]); t3=case["expected_top_cause"] in ranked[:3]
        correct+=c; top1+=t1; top3+=t3
        details.append({"case_id":case["case_id"],"expected_category":expected,"predicted_category":predicted,"classification_correct":c,"expected_top_cause":case["expected_top_cause"],"ranked_causes":ranked,"expected_cause_top1":t1,"expected_cause_top3":t3,"metrics_correlated":report["metric_correlation"]["matched"],"documentation_retrieved":len(report["documentation_evidence"]),"secret_redaction_check":"synthetic only"})
    n=len(cases)
    unknown_cases=[d for d in details if d["expected_category"]=="unknown"]
    summary={"dataset":"included synthetic scenarios","cases":n,"classification_accuracy":correct/n if n else 0,"expected_cause_top1_accuracy":top1/n if n else 0,"expected_cause_top3_accuracy":top3/n if n else 0,"metric_correlation_rate":sum(d["metrics_correlated"] for d in details)/n if n else 0,"unknown_cases":len(unknown_cases),"unknown_cases_classified_unknown":sum(1 for d in unknown_cases if d["predicted_category"]=="unknown"),"observed_classification_errors":[d["case_id"] for d in details if not d["classification_correct"]],"note":"Synthetic, deterministic smoke evaluation only. Do not present these figures as real-world or HCLTech production performance."}
    out={"summary":summary,"cases":details}
    (ROOT/"reports"/"synthetic_evaluation.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
    lines=["# Synthetic API Failure Diagnosis Evaluation","","> This is a deterministic smoke evaluation over included fictional scenarios; it is not a real-world benchmark or evidence of production accuracy.","",f"- Cases: {n}",f"- Classification accuracy: {summary['classification_accuracy']:.1%}",f"- Expected diagnosis ranked #1: {summary['expected_cause_top1_accuracy']:.1%}",f"- Expected diagnosis in top 3: {summary['expected_cause_top3_accuracy']:.1%}",f"- Metric correlation rate: {summary['metric_correlation_rate']:.1%}","","| Case | Expected | Predicted | Class correct | Expected diagnosis top 1 |", "|---|---|---|---:|---:|"]
    for d in details: lines.append(f"| {d['case_id']} | {d['expected_category']} | {d['predicted_category']} | {'Yes' if d['classification_correct'] else 'No'} | {'Yes' if d['expected_cause_top1'] else 'No'} |")
    lines += ["", "## Scenario coverage", "", "The suite includes 4xx validation, 5xx server, authentication, authorization, rate limiting, timeout and dependency failure cases. It also includes an incomplete/unsupported case with no status, timestamp, metrics or applicable docs; the expected behaviour is an `unknown` classification with information still required.", "", "## Observed errors", ""]
    if summary["observed_classification_errors"]:
        lines += [f"- Classification mismatches: {', '.join(summary['observed_classification_errors'])}."]
    else:
        lines += ["- No classification mismatch occurred in this deterministic synthetic run."]
    lines += [f"- Unsupported/incomplete cases correctly classified as unknown: {summary['unknown_cases_classified_unknown']}/{summary['unknown_cases']}.", "- The automated test suite covers parser formats, redaction, metric endpoint/time joins, documentation retrieval, report export, diagnosis ranking and reviewer feedback.", "", "## Limitations", "", "- The synthetic set is small and deliberately explicit; results are not a generalization estimate or production accuracy claim.", "- Cause scores/confidence labels and metric thresholds are heuristic, not calibrated probabilities or service-specific SLO thresholds.", "- Metric correlation is not proof of causality; missing/late metrics and clock skew can weaken conclusions.", "- BM25 + TF-IDF is lightweight lexical retrieval and can miss paraphrases with low term overlap.", "- Redaction is pattern-based best effort; inspect outputs and scrub source logs upstream.", "- A human reviewer must confirm/reject diagnoses before operational action; this assistant executes no remediation.", ""]
    (ROOT/"reports"/"SYNTHETIC_EVALUATION.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))
    if correct!=n: raise SystemExit(1)
if __name__=="__main__": main()
