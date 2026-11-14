"""CLI entry point for quick local synthetic analysis."""
import json
from .synthetic import list_scenarios,load_scenario,load_synthetic_documents
from .engine import analyze_case

if __name__ == "__main__":
    case=load_scenario(list_scenarios()[0]["case_id"])
    report=analyze_case(case,documents=load_synthetic_documents(),use_groq=False)
    print(json.dumps(report,indent=2,default=str))
