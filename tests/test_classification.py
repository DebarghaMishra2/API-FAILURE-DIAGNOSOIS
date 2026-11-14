import unittest
from app.classification import classify_failure
class ClassificationTests(unittest.TestCase):
 def test_required_categories(self):
  cases=[(401,"invalid token","authentication"),(403,"insufficient scope","authorization"),(422,"invalid field","validation"),(429,"quota exceeded","rate_limiting"),(504,"gateway timeout","timeout"),(503,"upstream connection refused","dependency_error"),(500,"internal server error","server_error")]
  for status,msg,expected in cases:
   with self.subTest(status=status): self.assertEqual(classify_failure({"status_code":status},msg)["category"],expected)
 def test_unknown_is_qualified(self):
  result=classify_failure({},"")
  self.assertEqual(result["category"],"unknown")
  self.assertTrue(result["reasons"])
