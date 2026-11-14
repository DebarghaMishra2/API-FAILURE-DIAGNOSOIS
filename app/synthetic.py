"""Load included synthetic API failure cases and API documentation."""
from pathlib import Path
import json
from .ingestion import parse_document_upload
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"synthetic"

def list_scenarios():
    path=DATA/"cases"/"scenarios.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []

def load_scenario(case_id):
    for case in list_scenarios():
        if case.get("case_id")==case_id: return case
    raise KeyError(case_id)

def load_synthetic_documents():
    docs=[]
    for path in sorted((DATA/"api_docs").iterdir()):
        if path.is_file(): docs.append(parse_document_upload(path.name,path.read_bytes()))
    return docs
