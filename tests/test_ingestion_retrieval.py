import unittest
from app.ingestion import parse_document_upload,parse_structured_file,parse_log_uploads,parse_metric_uploads
from app.retrieval import DocumentationRetriever
class IngestionTests(unittest.TestCase):
 def test_markdown_metadata_and_sections(self):
  raw=b"# API Guide\n\nVersion: 2.0\nEffective Date: 2026-01-01\nOwner: Platform\n\n## Authentication\n\nHTTP 401 means invalid token."
  d=parse_document_upload("guide.md",raw)
  self.assertEqual(d["metadata"]["version"],"2.0")
  self.assertTrue(any(c["section"]=="Authentication" for c in d["chunks"]))
 def test_html_table_rows_preserved(self):
  raw=b"<h1>Limit Guide</h1><p>Version: 1</p><table><tr><th>Plan</th><th>Limit</th></tr><tr><td>Basic</td><td>100</td></tr></table>"
  d=parse_document_upload("limits.html",raw)
  text=" ".join(c["text"] for c in d["chunks"])
  self.assertIn("Basic",text); self.assertIn("100",text)
 def test_txt_and_structured_parsing(self):
  d=parse_document_upload("errors.txt",b"API Errors\nHTTP 503 upstream unavailable")
  self.assertTrue(d["chunks"])
  rows=parse_structured_file("logs.json",b'{"records":[{"method":"GET","path":"/x","status":401}]}')
  self.assertEqual(len(rows),1)
  logs=parse_log_uploads([("a.csv",b"method,endpoint,status_code\nGET,/x,401\n")])
  self.assertEqual(logs[0]["status_code"],"401")
  self.assertEqual(logs[0]["source_file"],"a.csv")
  metrics=parse_metric_uploads([("metrics.csv",b"timestamp,endpoint,error_rate_pct\n2026-11-14T09:00:00Z,/x,5\n")])
  self.assertEqual(metrics[0]["source_file"],"metrics.csv")
 def test_pdf_extraction(self):
  try:
   from reportlab.pdfgen import canvas
   import io
   b=io.BytesIO(); c=canvas.Canvas(b); c.drawString(70,750,"API PDF Guide"); c.drawString(70,720,"HTTP 429 Too Many Requests"); c.save()
   d=parse_document_upload("errors.pdf",b.getvalue())
   self.assertTrue(d["chunks"])
  except ImportError: self.skipTest("reportlab not installed")
 def test_request_and_response_events_join_by_correlation_id(self):
  req=b'{"event_type":"request","timestamp":"2026-11-14T09:00:00Z","correlation_id":"CORR-1","method":"GET","endpoint":"/v1/orders","headers":{"Accept":"application/json"}}'
  resp=b'{"event_type":"response","timestamp":"2026-11-14T09:00:01Z","correlation_id":"CORR-1","status_code":429,"latency_ms":12,"headers":{"Retry-After":"30"}}'
  joined=parse_log_uploads([("request.jsonl",req),("response.jsonl",resp)])
  self.assertEqual(len(joined),1)
  self.assertEqual(joined[0]["status_code"],429)
  self.assertIn("accept",[k.lower() for k in joined[0]["request_headers"]])
  self.assertEqual(joined[0]["response_headers"].get("Retry-After"),"30")
 def test_doc_retrieval_returns_source_metadata(self):
  chunks=[{"text":"HTTP 429 Too Many Requests; honor Retry-After header.","source":"limits.md","title":"Rate Limits","section":"429","page":None,"metadata":{"version":"1"}}]
  r=DocumentationRetriever(chunks).search("quota exceeded and Retry-After",top_k=1)
  self.assertEqual(r[0]["source"],"limits.md"); self.assertIn("retrieval_score",r[0])
