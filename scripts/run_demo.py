from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app.synthetic import list_scenarios,load_scenario,load_synthetic_documents
from app.engine import analyze_case
from app.reporting import to_markdown
if __name__=="__main__":
    for case in list_scenarios():
        report=analyze_case(case,documents=load_synthetic_documents(),use_groq=False)
        print(to_markdown(report))
