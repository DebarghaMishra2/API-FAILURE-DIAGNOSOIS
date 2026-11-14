"""Reviewer feedback persistence using SQLite."""
from __future__ import annotations
import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone

def init_db(db_path="data/feedback.sqlite3"):
    path=Path(db_path); path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE IF NOT EXISTS diagnosis_feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, report_id TEXT NOT NULL, decision TEXT NOT NULL CHECK(decision IN ('confirmed','rejected','annotated')), annotation TEXT, reviewer TEXT, created_at TEXT NOT NULL, diagnosis_json TEXT NOT NULL)")

def save_feedback(report_id,decision,annotation="",reviewer="reviewer",diagnosis=None,db_path="data/feedback.sqlite3"):
    if decision not in {"confirmed","rejected","annotated"}: raise ValueError("Invalid feedback decision")
    init_db(db_path)
    with sqlite3.connect(db_path) as con:
        cur=con.execute("INSERT INTO diagnosis_feedback(report_id,decision,annotation,reviewer,created_at,diagnosis_json) VALUES(?,?,?,?,?,?)",(report_id,decision,annotation[:2000],reviewer[:100],datetime.now(timezone.utc).isoformat(),json.dumps(diagnosis or {},default=str)))
        return cur.lastrowid

def list_feedback(db_path="data/feedback.sqlite3"):
    init_db(db_path)
    with sqlite3.connect(db_path) as con:
        con.row_factory=sqlite3.Row
        return [dict(r) for r in con.execute("SELECT * FROM diagnosis_feedback ORDER BY id DESC")]
