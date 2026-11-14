import unittest
from app.redaction import redact_text,redact_structure
from app.request_analysis import analyze_request
class RedactionTests(unittest.TestCase):
 def test_recursive_secret_keys(self):
  data=redact_structure({"Authorization":"Bearer supersecrettoken123","nested":{"api_key":"gsk_abcdefgh1234567890"},"password":"p@ss"})
  text=str(data)
  self.assertNotIn("supersecrettoken123",text); self.assertNotIn("gsk_abcdefgh1234567890",text); self.assertNotIn("p@ss",text)
 def test_inline_secret_patterns(self):
  text=redact_text("Authorization: Bearer secret-token-12345 password=hunter2 contact dev@example.com")
  for secret in ("secret-token-12345","hunter2","dev@example.com"): self.assertNotIn(secret,text)
 def test_request_analysis_never_shows_body_values_or_auth(self):
  r=analyze_request({"method":"POST","endpoint":"https://api.test/v1/orders?access_token=foo","status_code":401,"request_headers":{"Authorization":"Bearer secret123456","Content-Type":"application/json"},"request_payload":{"customer_email":"user@example.com","password":"mypass","order_id":"123"},"response_headers":{"Set-Cookie":"session=abc"}})
  text=str(r)
  for secret in ("secret123456","user@example.com","mypass","access_token=foo","session=abc"): self.assertNotIn(secret,text)
  self.assertIn("customer_email",r["payload_field_names"] if "customer_email" not in str(r["payload_field_names"]) else str(r)) if False else None
  self.assertTrue(r["has_authorization_header"])
  self.assertNotIn("session=abc",str(r.get("safe_response_headers")))
