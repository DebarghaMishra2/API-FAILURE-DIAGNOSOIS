import tempfile,unittest
from pathlib import Path
from app.synthetic import load_scenario,load_synthetic_documents
from app.engine import analyze_case
from app.reporting import to_json,to_markdown
from app.feedback import save_feedback,list_feedback
class ReportFeedbackTests(unittest.TestCase):
 def test_exports_are_redacted_and_auditable(self):
  report=analyze_case(load_scenario("AUTH-401"),documents=load_synthetic_documents(),use_groq=False)
  js=to_json(report); md=to_markdown(report)
  self.assertIn("root_cause_confirmed",js); self.assertIn("Ranked diagnosis",md)
  self.assertNotIn("synthetic-token-value-123456",js+md)
  self.assertIn("redacted",(js+md).lower())
 def test_feedback_confirm_reject_annotate(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=str(Path(tmp)/"feedback.sqlite3")
   for decision in ("confirmed","rejected","annotated"):
    save_feedback("CASE-1",decision,"review note","judge",{"cause":"authentication"},db)
   rows=list_feedback(db)
   self.assertEqual(len(rows),3)
   self.assertEqual({r["decision"] for r in rows},{"confirmed","rejected","annotated"})
