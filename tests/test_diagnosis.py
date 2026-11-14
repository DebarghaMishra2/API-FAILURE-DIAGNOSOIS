import unittest
from app.synthetic import list_scenarios,load_scenario,load_synthetic_documents
from app.engine import analyze_case
class DiagnosisTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.docs=load_synthetic_documents()
 def test_all_synthetic_classifications(self):
  for case in list_scenarios():
   with self.subTest(case=case["case_id"]):
    report=analyze_case(case,documents=self.docs,use_groq=False)
    self.assertEqual(report["classification"]["category"],case["expected_category"])
    self.assertTrue(report["ranked_diagnoses"])
    self.assertEqual(report["root_cause_confirmed"],False)
 def test_rate_limit_response_header_is_safe_and_used(self):
  report=analyze_case(load_scenario("RATE-429"),documents=self.docs,use_groq=False)
  self.assertEqual(report["request_analysis"]["safe_response_headers"].get("x-ratelimit-remaining"),"0")
  self.assertEqual(report["ranked_diagnoses"][0]["cause"],"rate_limiting")
 def test_report_has_metric_and_doc_evidence(self):
  report=analyze_case(load_scenario("TIME-504"),documents=self.docs,use_groq=False)
  self.assertTrue(report["metric_correlation"]["matched"])
  self.assertTrue(report["documentation_evidence"])
  self.assertTrue(report["ranked_diagnoses"][0]["supporting_evidence"])
 def test_report_contains_uncertainty_not_confirmed_root_cause(self):
  case={"case_id":"MIN","event":{"method":"GET","endpoint":"/x","status_code":500}}
  report=analyze_case(case,documents=[],use_groq=False)
  self.assertFalse(report["root_cause_confirmed"])
  self.assertTrue(report["uncertainty"])
