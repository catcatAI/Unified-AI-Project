import unittest
from unittest.mock import patch, mock_open
import os
import glob
import ast # Ensure ast is imported for any direct ast comparisons if needed, though unparse is main

# Assuming src is in PYTHONPATH for test execution
from src.core_ai.code_understanding.lightweight_code_model import LightweightCodeModel

class TestLightweightCodeModel(unittest.TestCase):

    def setUp(self):
        self.mock_tools_dir = "src/tools/"
        self.model = LightweightCodeModel(tools_directory=self.mock_tools_dir)

    @patch('glob.glob')
    @patch('os.path.isdir')
    @patch('os.path.basename') # Mock basename as it's used by list_tool_files
    def test_list_tool_files(self, mock_os_path_basename, mock_os_path_isdir, mock_glob_glob):
        mock_os_path_isdir.return_value = True
        # Simulate glob finding these files
        glob_paths = [
            os.path.join(self.mock_tools_dir, "tool_one.py"),
            os.path.join(self.mock_tools_dir, "__init__.py"),
            os.path.join(self.mock_tools_dir, "tool_two.py"),
            os.path.join(self.mock_tools_dir, "tool_dispatcher.py"),
            os.path.join(self.mock_tools_dir, "subdir", "tool_three.py") # Test subdirectory case
        ]
        mock_glob_glob.return_value = glob_paths

        # Configure side_effect for os.path.basename
        mock_os_path_basename.side_effect = [
            "tool_one.py",
            "__init__.py",
            "tool_two.py",
            "tool_dispatcher.py",
            "tool_three.py"
        ]

        expected_files = [
            os.path.join(self.mock_tools_dir, "tool_one.py"),
            os.path.join(self.mock_tools_dir, "tool_two.py"),
            os.path.join(self.mock_tools_dir, "subdir", "tool_three.py")
        ]

        tool_files = self.model.list_tool_files()
        self.assertCountEqual(tool_files, expected_files, "Should list correct tool files, excluding __init__ and dispatcher.")
        mock_glob_glob.assert_called_once_with(os.path.join(self.mock_tools_dir, "**", "*.py"), recursive=True)


    @patch('os.path.isdir')
    def test_list_tool_files_non_existent_dir(self, mock_isdir):
        mock_isdir.return_value = False
        model = LightweightCodeModel(tools_directory="non_existent_dir/")
        tool_files = model.list_tool_files()
        self.assertEqual(tool_files, [])

    def test_analyze_tool_file_simple_class_and_function(self):
        sample_code = """
import typing
from typing import List, Optional

class SimpleTool:
    \"\"\"A simple tool class docstring.\"\"\"
    def __init__(self, name: str = "Tool"):
        \"\"\"Initializer docstring.\"\"\"
        self.name = name

    async def execute(self, value: int, details: Optional[dict] = None) -> str:
        \"\"\"Execute method docstring.

        Args:
            value (int): The value to process.
            details (Optional[dict]): Optional details.

        Returns:
            str: The processed value as a string.
        \"\"\"
        return f"{self.name} processed {value} with {details}"

def module_level_func(x: float, *args, y: float = 3.14, **kwargs) -> List[float]:
    \"\"\"Module level function docstring.\"\"\"
    return [x * y] + list(args)
"""
        m = mock_open(read_data=sample_code)
        with patch('builtins.open', m), \
             patch('os.path.isfile', return_value=True):
            analysis_result = self.model.analyze_tool_file("dummy_path/simple_tool.py")

        self.assertIsNotNone(analysis_result)
        self.assertEqual(analysis_result["filepath"], "dummy_path/simple_tool.py")

        # Class assertions
        self.assertEqual(len(analysis_result["classes"]), 1)
        simple_tool_class = analysis_result["classes"][0]
        self.assertEqual(simple_tool_class["name"], "SimpleTool")
        self.assertEqual(simple_tool_class["docstring"], "A simple tool class docstring.")
        self.assertEqual(len(simple_tool_class["methods"]), 2)

        # __init__ method
        init_method = next(mthd for mthd in simple_tool_class["methods"] if mthd["name"] == "__init__")
        self.assertEqual(init_method["docstring"], "Initializer docstring.")
        expected_init_params = [
            {"name": "self", "annotation": None, "default": None},
            {"name": "name", "annotation": "str", "default": "'Tool'"} # Changed to single quotes based on ast.unparse behavior
        ]
        self.assertListEqual(init_method["parameters"], expected_init_params)
        self.assertIsNone(init_method["returns"])

        # execute method (async)
        execute_method = next(mthd for mthd in simple_tool_class["methods"] if mthd["name"] == "execute")
        self.assertTrue("Execute method docstring." in execute_method["docstring"])
        expected_execute_params = [
            {"name": "self", "annotation": None, "default": None},
            {"name": "value", "annotation": "int", "default": None},
            {"name": "details", "annotation": "Optional[dict]", "default": "None"}
        ]
        self.assertListEqual(execute_method["parameters"], expected_execute_params)
        self.assertEqual(execute_method["returns"], "str")

        # Module-level function assertions
        self.assertEqual(len(analysis_result["functions"]), 1)
        module_func = analysis_result["functions"][0]
        self.assertEqual(module_func["name"], "module_level_func")
        self.assertEqual(module_func["docstring"], "Module level function docstring.")
        expected_module_params = [
            {"name": "x", "annotation": "float", "default": None},
            {"name": "y", "annotation": "float", "default": "3.14"}, # kwonlyarg
            {"name": "*args", "annotation": None, "default": None},
            {"name": "**kwargs", "annotation": None, "default": None}
        ]
        # Order of *args, **kwargs might vary based on extraction method, so check presence and details.
        # For now, assuming current order from _extract_method_parameters (pos, kwonly, vararg, kwarg)
        # Let's sort by name for comparison for args, vararg, kwarg
        param_names_from_result = sorted([p["name"] for p in module_func["parameters"]])
        expected_param_names = sorted([p["name"] for p in expected_module_params])
        self.assertListEqual(param_names_from_result, expected_param_names)

        for p_expected in expected_module_params:
            p_actual = next(p for p in module_func["parameters"] if p["name"] == p_expected["name"])
            self.assertEqual(p_actual["annotation"], p_expected["annotation"])
            self.assertEqual(p_actual["default"], p_expected["default"])

        self.assertEqual(module_func["returns"], "List[float]")


    def test_analyze_tool_file_no_classes_or_functions(self):
        sample_code = "# Just comments and variables\nPI = 3.14"
        m = mock_open(read_data=sample_code)
        with patch('builtins.open', m), \
             patch('os.path.isfile', return_value=True):
            analysis_result = self.model.analyze_tool_file("dummy_path/empty_tool.py")

        self.assertIsNotNone(analysis_result)
        self.assertEqual(len(analysis_result["classes"]), 0)
        self.assertEqual(len(analysis_result["functions"]), 0)

    def test_analyze_tool_file_parsing_error(self):
        sample_code = "def func(a: int -> str:" # Syntax error
        m = mock_open(read_data=sample_code)
        with patch('builtins.open', m), \
             patch('os.path.isfile', return_value=True):
            analysis_result = self.model.analyze_tool_file("dummy_path/error_tool.py")
        self.assertIsNone(analysis_result, "Should return None on parsing error.")

    def test_analyze_tool_file_not_found(self):
        with patch('os.path.isfile', return_value=False):
            analysis_result = self.model.analyze_tool_file("non_existent_file.py")
        self.assertIsNone(analysis_result)

    @patch('os.path.isfile')
    def test_get_tool_structure_direct_path(self, mock_isfile):
        mock_isfile.return_value = True
        with patch.object(self.model, 'analyze_tool_file', return_value={"mocked": "analysis"}) as mock_analyze:
            result = self.model.get_tool_structure("src/tools/some_tool.py")
            mock_analyze.assert_called_once_with("src/tools/some_tool.py")
            self.assertEqual(result, {"mocked": "analysis"})

    @patch('os.path.join')
    @patch('os.path.isfile')
    def test_get_tool_structure_tool_name_resolution(self, mock_isfile, mock_join):
        mock_isfile.side_effect = [False, True]
        resolved_path = os.path.join(self.mock_tools_dir, "my_tool.py")
        mock_join.return_value = resolved_path

        with patch.object(self.model, 'analyze_tool_file', return_value={"resolved": "analysis"}) as mock_analyze:
            result = self.model.get_tool_structure("my_tool")
            # Check if the specific call we care about was made, among potentially others
            self.assertIn(unittest.mock.call(self.mock_tools_dir, "my_tool"), mock_join.call_args_list)
            mock_analyze.assert_called_once_with(resolved_path)
            self.assertEqual(result, {"resolved": "analysis"})

    @patch('os.path.isfile', return_value=False)
    def test_get_tool_structure_tool_not_found(self, mock_isfile):
        with patch.object(self.model, 'analyze_tool_file') as mock_analyze:
            result = self.model.get_tool_structure("non_existent_tool")
            mock_analyze.assert_not_called()
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
