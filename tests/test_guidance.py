import unittest
from app.guidance import diagnostic_guidance
class GuidanceTests(unittest.TestCase):
 def test_all_categories_have_guidance(self):
  for c in ["authentication","authorization","validation","rate_limiting","timeout","dependency_error","server_error","not_found","unknown"]:
   result=diagnostic_guidance(c)
   self.assertTrue(result["verification_steps"])
   self.assertFalse(result["automation_performed"])
   self.assertIn("authorized operator",result["escalation"])
 def test_no_mutating_action_as_automatic_guidance(self):
  text=" ".join(diagnostic_guidance("server_error")["verification_steps"]).lower()
  self.assertNotIn("restart the service",text)
  self.assertNotIn("rotate the credential",text)
