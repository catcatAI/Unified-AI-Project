import unittest
import pytest
from unittest.mock import patch, mock_open
import os
import glob
import ast # Ensure ast is imported for any direct ast comparisons if needed, though unparse is main
import tempfile # For temporary directory
import logging # For self.assertLogs

# 修复导入路径
from apps.backend.src.core_ai.code_understanding.lightweight_code_model import LightweightCodeModel

class TestLightweightCodeModel(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for tools
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_tools_dir = self.temp_dir_obj.name
        self.model = LightweightCodeModel(tools_directory=self.temp_tools_dir)
        # It's good practice to also capture logs if the module emits them during tests
        # self.logger_patcher = patch('apps.backend.src.ai.code_understanding.lightweight_code_model.logger')
        # self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir_obj.cleanup()
        # self.logger_patcher.stop()

    @pytest.mark.timeout(5)
    def test_list_tool_files(self):
        # Create dummy files and a subdirectory in the temp_tools_dir
        self._create_dummy_tool_file("tool_one.py")
        self._create_dummy_tool_file("__init__.py") # Should be excluded
        self._create_dummy_tool_file("tool_two.py")
        self._create_dummy_tool_file("tool_dispatcher.py") # Should be excluded

        subdir = os.path.join(self.temp_tools_dir, "subdir")
        os.makedirs(subdir)
        self._create_dummy_tool_file(os.path.join("subdir", "tool_three.py"))
        self._create_dummy_tool_file(os.path.join("subdir", "another_tool.py"))
        self._create_dummy_tool_file(os.path.join("subdir", "__init__.py")) # Excluded from subdir too

        # Non-python file
        with open(os.path.join(self.temp_tools_dir, "data.txt"), "w") as f:
            f.write("text")

        expected_files = [
            os.path.join(self.temp_tools_dir, "tool_one.py"),
            os.path.join(self.temp_tools_dir, "tool_two.py"),
            os.path.join(self.temp_tools_dir, "subdir", "tool_three.py"),
            os.path.join(self.temp_tools_dir, "subdir", "another_tool.py")
        ]

        tool_files = self.model.list_tool_files()
        self.assertCountEqual(tool_files, expected_files,
                              "Should list correct tool files, excluding __init__ and dispatcher, and include those in subdirs.")

    @pytest.mark.timeout(5)
    def test_list_tool_files_non_existent_dir(self):
        # This test now implicitly uses the logger due to changes in __init__
        with self.assertLogs(logger='apps.backend.src.core_ai.code_understanding.lightweight_code_model', level='WARNING') as cm:
            model = LightweightCodeModel(tools_directory="non_existent_dir_for_list_test/")
        self.assertTrue(any("Tools directory 'non_existent_dir_for_list_test/' does not exist" in record.getMessage() for record in cm.records))

        tool_files = model.list_tool_files() # Should return empty list as dir doesn't exist
        self.assertEqual(tool_files, [])

    @pytest.mark.timeout(5)
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
        self.assertEqual(analysis_result.filepath, "dummy_path/simple_tool.py")

        # Class assertions
        self.assertEqual(len(analysis_result.classes), 1)
        simple_tool_class = analysis_result.classes[0]
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
        self.assertEqual(len(analysis_result.functions), 1)
        module_func = analysis_result.functions[0]
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


    @pytest.mark.timeout(5)
    def test_analyze_tool_file_no_classes_or_functions(self):
        sample_code = "# Just comments and variables\nPI = 3.14"
        m = mock_open(read_data=sample_code)
        with patch('builtins.open', m), \
             patch('os.path.isfile', return_value=True):
            analysis_result = self.model.analyze_tool_file("dummy_path/empty_tool.py")

        self.assertIsNotNone(analysis_result)
        self.assertEqual(len(analysis_result.classes), 0)
        self.assertEqual(len(analysis_result.functions), 0)

    @pytest.mark.timeout(5)
    def test_analyze_tool_file_parsing_error(self):
        sample_code = "def func(a: int -> str:" # Syntax error
        m = mock_open(read_data=sample_code)
        with patch('builtins.open', m), \
             patch('os.path.isfile', return_value=True):
            analysis_result = self.model.analyze_tool_file("dummy_path/error_tool.py")
        self.assertIsNone(analysis_result, "Should return None on parsing error.")

    @pytest.mark.timeout(5)
    def test_analyze_tool_file_not_found(self):
        with patch('os.path.isfile', return_value=False):
            analysis_result = self.model.analyze_tool_file("non_existent_file.py")
        self.assertIsNone(analysis_result)

    # --- Tests for get_tool_structure name resolution ---

    def _create_dummy_tool_file(self, filename: str, content: str = "def main(): pass"):
        filepath = os.path.join(self.temp_tools_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        return filepath

    @pytest.mark.timeout(5)
    def test_get_tool_structure_direct_valid_path(self):
        dummy_tool_path = self._create_dummy_tool_file("actual_tool.py")
        # We mock analyze_tool_file to isolate testing of path resolution logic
        with patch.object(self.model, 'analyze_tool_file', return_value={"analysis": "done"}) as mock_analyze:
            result = self.model.get_tool_structure(dummy_tool_path)
            mock_analyze.assert_called_once_with(dummy_tool_path)
            self.assertEqual(result, {"analysis": "done"})

    @pytest.mark.timeout(5)
    def test_get_tool_structure_direct_invalid_path(self):
        invalid_path = os.path.join(self.temp_tools_dir, "non_existent_tool.py")
        with self.assertLogs(logger='apps.backend.src.core_ai.code_understanding.lightweight_code_model', level='WARNING') as cm:
            result = self.model.get_tool_structure(invalid_path)
            self.assertIsNone(result)
        self.assertTrue(any(f"appears to be a path but was not found" in record.getMessage() for record in cm.records))

    @pytest.mark.timeout(5)
    def test_get_tool_structure_path_looks_like_path_but_not_found(self):
        # This tests the case where the input string contains path separators but doesn't exist
        path_like_non_existent = "some_dir/non_existent_tool.py"
        # Ensure this path doesn't accidentally exist relative to where test runs
        self.assertFalse(os.path.isfile(path_like_non_existent))

        with self.assertLogs(logger='apps.backend.src.core_ai.code_understanding.lightweight_code_model', level='WARNING') as cm:
            result = self.model.get_tool_structure(path_like_non_existent)
        self.assertIsNone(result)
        self.assertTrue(any(f"appears to be a path but was not found" in record.getMessage() for record in cm.records))

    @pytest.mark.timeout(5)
    def test_get_tool_structure_resolve_exact_name_dot_py(self):
        self._create_dummy_tool_file("exact_match.py")
        with patch.object(self.model, 'analyze_tool_file', return_value={"analyzed": "exact_match.py"}) as mock_analyze:
            # Test with extension
            result_with_ext = self.model.get_tool_structure("exact_match.py")
            mock_analyze.assert_called_with(os.path.join(self.temp_tools_dir, "exact_match.py"))
            self.assertEqual(result_with_ext, {"analyzed": "exact_match.py"})

            mock_analyze.reset_mock()
            # Test without extension
            result_without_ext = self.model.get_tool_structure("exact_match")
            mock_analyze.assert_called_with(os.path.join(self.temp_tools_dir, "exact_match.py"))
            self.assertEqual(result_without_ext, {"analyzed": "exact_match.py"})

    @pytest.mark.timeout(5)
    def test_get_tool_structure_resolve_tool_prefix_pattern(self):
        self._create_dummy_tool_file("tool_sample_prefix.py")
        with patch.object(self.model, 'analyze_tool_file', return_value={"analyzed": "tool_sample_prefix.py"}) as mock_analyze:
            result = self.model.get_tool_structure("sample_prefix")
            mock_analyze.assert_called_once_with(os.path.join(self.temp_tools_dir, "tool_sample_prefix.py"))
            self.assertEqual(result, {"analyzed": "tool_sample_prefix.py"})

    @pytest.mark.timeout(5)
    def test_get_tool_structure_resolve_suffix_tool_pattern(self):
        self._create_dummy_tool_file("sample_suffix_tool.py")
        with patch.object(self.model, 'analyze_tool_file', return_value={"analyzed": "sample_suffix_tool.py"}) as mock_analyze:
            result = self.model.get_tool_structure("sample_suffix")
            mock_analyze.assert_called_once_with(os.path.join(self.temp_tools_dir, "sample_suffix_tool.py"))
            self.assertEqual(result, {"analyzed": "sample_suffix_tool.py"})

    @pytest.mark.timeout(5)
    def test_get_tool_structure_prefers_exact_over_pattern(self):
        self._create_dummy_tool_file("pref_exact.py", content="# exact content")
        self._create_dummy_tool_file("tool_pref_exact.py", content="# tool_prefix content")
        # analyze_tool_file will be mocked to return the path it was called with for simplicity
        def side_effect_analyzer(filepath, dna_chain_id=None): return {"path": filepath}

        with patch.object(self.model, 'analyze_tool_file', side_effect=side_effect_analyzer) as mock_analyze:
            result = self.model.get_tool_structure("pref_exact")
            # It should find "pref_exact.py" directly
            mock_analyze.assert_called_once_with(os.path.join(self.temp_tools_dir, "pref_exact.py"))
            self.assertEqual(result, {"path": os.path.join(self.temp_tools_dir, "pref_exact.py")})

    @pytest.mark.timeout(5)
    def test_get_tool_structure_ambiguous_patterns(self):
        self._create_dummy_tool_file("tool_ambiguous_pattern.py")
        self._create_dummy_tool_file("ambiguous_pattern_tool.py")
        with self.assertLogs(logger='apps.backend.src.core_ai.code_understanding.lightweight_code_model', level='WARNING') as cm:
            result = self.model.get_tool_structure("ambiguous_pattern")
        self.assertIsNone(result)
        self.assertTrue(any("Ambiguous tool name 'ambiguous_pattern'" in record.getMessage() for record in cm.records))

    @pytest.mark.timeout(5)
    def test_get_tool_structure_name_not_found(self):
        with self.assertLogs(logger='apps.backend.src.core_ai.code_understanding.lightweight_code_model', level='WARNING') as cm:
            result = self.model.get_tool_structure("completely_non_existent_tool_name")
        self.assertIsNone(result)
        self.assertTrue(any("Could not resolve tool 'completely_non_existent_tool_name'" in record.getMessage() for record in cm.records))

    @pytest.mark.timeout(5)
    def test_get_tool_structure_invalid_tools_directory(self):
        bad_dir_path = "path_that_does_not_exist_at_all_xyz"

        # Test log during __init__
        with self.assertLogs(logger='apps.backend.src.core_ai.code_understanding.lightweight_code_model', level='WARNING') as init_cm:
            model_bad_dir = LightweightCodeModel(tools_directory=bad_dir_path)
        self.assertTrue(any(f"Tools directory '{bad_dir_path}' does not exist or is not a directory." in record.getMessage() for record in init_cm.records))

        # Test log during get_tool_structure
        with self.assertLogs(logger='apps.backend.src.core_ai.code_understanding.lightweight_code_model', level='WARNING') as get_cm:
            result = model_bad_dir.get_tool_structure("any_tool_name")
        self.assertIsNone(result)
        self.assertTrue(any(f"Tools directory '{bad_dir_path}' is not valid. Cannot resolve tool by name: any_tool_name" in record.getMessage() for record in get_cm.records))


if __name__ == '__main__':
    unittest.main()