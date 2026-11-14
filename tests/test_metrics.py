import unittest
from app.metrics import correlate_metrics
class MetricTests(unittest.TestCase):
 def test_same_endpoint_and_window_match(self):
  metrics=[{"timestamp":"2026-11-14T09:00:30Z","endpoint":"/v1/orders/555","p95_latency_ms":1800,"error_rate_pct":8}]
  r=correlate_metrics("/v1/orders/123","2026-11-14T09:00:00Z",metrics,300)
  self.assertTrue(r["matched"]); self.assertEqual(r["time_match"],"within_window"); self.assertTrue(r["anomalies"])
 def test_wrong_endpoint_does_not_match(self):
  r=correlate_metrics("/v1/orders","2026-11-14T09:00:00Z",[{"timestamp":"2026-11-14T09:00:00Z","endpoint":"/v1/users","p95_latency_ms":10}])
  self.assertFalse(r["matched"])
 def test_out_of_window_does_not_match(self):
  r=correlate_metrics("/v1/orders","2026-11-14T09:00:00Z",[{"timestamp":"2026-11-14T10:00:00Z","endpoint":"/v1/orders"}],60)
  self.assertFalse(r["matched"])
