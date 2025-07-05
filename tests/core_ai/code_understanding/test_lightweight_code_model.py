import unittest
import os
import sys

# Add src directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..")) # Unified-AI-Project/
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core_ai.code_understanding.lightweight_code_model import LightweightCodeModel

class TestLightweightCodeModel(unittest.TestCase):

    def setUp(self):
        self.lcm = LightweightCodeModel()

    def test_01_initialization(self):
        self.assertIsNotNone(self.lcm)
        print("TestLightweightCodeModel.test_01_initialization PASSED")

    def test_02_check_syntax_python(self):
        valid_py_code = "def foo():\n  return 'bar'"
        result_valid = self.lcm.check_syntax(valid_py_code, "python")
        self.assertEqual(result_valid["status"], "valid")
        self.assertEqual(len(result_valid["errors"]), 0)

        invalid_py_code = "def foo():\n  return bar" # bar not defined, but syntax is fine for ast.parse
                                                 # ast.parse checks syntax, not semantics like undefined vars.
                                                 # Let's use a clearer syntax error.
        invalid_py_code_syntax = "def foo()\n  print 'hello'" # Missing colon, Python 2 print
        result_invalid_syntax = self.lcm.check_syntax(invalid_py_code_syntax, "python")
        self.assertEqual(result_invalid_syntax["status"], "invalid")
        self.assertGreater(len(result_invalid_syntax["errors"]), 0)
        if result_invalid_syntax["errors"]: # Check error details if list is not empty
            self.assertIn("message", result_invalid_syntax["errors"][0])
            # self.assertIn("line", result_invalid_syntax["errors"][0]) # ast.SyntaxError has lineno

        # Test with an empty string - ast.parse considers this valid (empty module)
        empty_code = ""
        result_empty = self.lcm.check_syntax(empty_code, "python")
        self.assertEqual(result_empty["status"], "valid")
        self.assertEqual(len(result_empty["errors"]), 0)

        print("TestLightweightCodeModel.test_02_check_syntax_python PASSED")

    def test_03_check_syntax_javascript_placeholder(self):
        # Test JS placeholder logic
        valid_js_like = "function foo() { return 'bar'; }"
        result_valid_js = self.lcm.check_syntax(valid_js_like, "javascript")
        self.assertEqual(result_valid_js["status"], "valid")
        self.assertIn("note", result_valid_js) # Placeholder often adds a note

        unbalanced_js = "function foo() { return 'bar';" # Missing closing }
        result_unbalanced_js = self.lcm.check_syntax(unbalanced_js, "javascript")
        self.assertEqual(result_unbalanced_js["status"], "invalid")
        self.assertTrue(any("Unbalanced" in err.get("message","") for err in result_unbalanced_js["errors"]))
        print("TestLightweightCodeModel.test_03_check_syntax_javascript_placeholder PASSED")

    def test_04_check_syntax_other_language_placeholder(self):
        other_code = "int main() { return 0; }"
        result_other = self.lcm.check_syntax(other_code, "c++")
        self.assertEqual(result_other["status"], "valid") # Placeholder returns valid
        self.assertIn("note", result_other)
        self.assertTrue("placeholder" in result_other["note"].lower())
        print("TestLightweightCodeModel.test_04_check_syntax_other_language_placeholder PASSED")

    def test_05_generate_boilerplate(self):
        # Python class
        py_class = self.lcm.generate_boilerplate("class", "python")
        self.assertIn("class NewClass:", py_class)
        self.assertIn("def __init__(self):", py_class)

        # JS function
        js_func = self.lcm.generate_boilerplate("function", "javascript")
        self.assertIn("function newFunction(arg1, arg2)", js_func)
        self.assertIn("// TODO: Implement", js_func)

        # HTML basic page
        html_page = self.lcm.generate_boilerplate("basic_page", "html")
        self.assertIn("<!DOCTYPE html>", html_page)
        self.assertIn("<h1>Hello, World!</h1>", html_page)

        # Unknown template
        unknown_py = self.lcm.generate_boilerplate("struct", "python")
        self.assertIn("not defined", unknown_py)

        # Unknown language
        unknown_lang = self.lcm.generate_boilerplate("class", "ruby")
        self.assertIn("not available", unknown_lang)
        print("TestLightweightCodeModel.test_05_generate_boilerplate PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)
