import unittest
import pytest
from unittest.mock import patch, MagicMock
import os

from apps.backend.src.tools.code_understanding_tool import CodeUnderstandingTool
from apps.backend.src.ai.code_understanding.lightweight_code_model import LightweightCodeModel

class TestCodeUnderstandingTool(unittest.TestCase):

    def setUp(self):
        # Create a mock instance for LightweightCodeModel
        self.mock_lwm_instance = MagicMock(spec=LightweightCodeModel)

        # Patch the LightweightCodeModel class specifically where it's imported by CodeUnderstandingTool
        self.lwm_patcher = patch('src.tools.code_understanding_tool.LightweightCodeModel', return_value=self.mock_lwm_instance)
        # Start the patcher and keep a reference to the Mock Class if needed, though instance is usually enough
        self.MockLWMClass = self.lwm_patcher.start()
        self.addCleanup(self.lwm_patcher.stop) # Ensure patch is stopped after test method

        # Instantiate the tool, which will now use self.mock_lwm_instance
        self.tool = CodeUnderstandingTool()

    @pytest.mark.timeout(5)
    def test_list_tools_success(self):
        # Configure the mock_lwm_instance (which is self.tool.code_model)
        mock_tool_files = [
            os.path.join("dummy/tools", "math_tool.py"), # Note: self.tool.tools_directory is not used by mock
            os.path.join("dummy/tools", "another_tool.py"),
            os.path.join("dummy/tools", "subdir", "sub_tool.py")
        ]
        self.mock_lwm_instance.list_tool_files.return_value = mock_tool_files

        expected_output = "Available Python tools: another_tool, math_tool, sub_tool."
        result = self.tool.execute("list_tools")

        self.assertEqual(result, expected_output)
        self.mock_lwm_instance.list_tool_files.assert_called_once()

    @pytest.mark.timeout(5)
    def test_list_tools_no_tools_found(self):
        self.mock_lwm_instance.list_tool_files.return_value = []

        expected_output = "No Python tools found in the tools directory."
        result = self.tool.execute("list_tools")

        self.assertEqual(result, expected_output)

    @pytest.mark.timeout(5)
    def test_describe_tool_found(self): # Removed @patch('os.path.isfile')
        tool_name = "math_tool"

        mock_structure = {
            "filepath": f"dummy/tools/{tool_name}.py",
            "classes": [
                {
                    "name": "MathTool",
                    "docstring": "Performs math.",
                    "methods": [
                        {
                            "name": "execute",
                            "docstring": "Runs calculation.",
                            "parameters": [
                                {"name": "self", "annotation": None, "default": None},
                                {"name": "expr", "annotation": "str", "default": None}
                            ],
                            "returns": "float"
                        }
                    ]
                }
            ],
            "functions": []
        }
        self.mock_lwm_instance.get_tool_structure.return_value = mock_structure

        result = self.tool.execute("describe_tool", tool_name=tool_name)

        self.assertIn(f"Description for tool '{tool_name}'", result)
        self.assertIn("Class: MathTool", result)
        self.assertIn("Docstring: Performs math.", result)
        self.assertIn("Methods:", result)
        self.assertIn("- execute(self, expr: str) -> float", result) # Check formatting
        self.assertIn("Docstring:\n        Runs calculation.", result)
        self.mock_lwm_instance.get_tool_structure.assert_called_once_with(tool_name)

    @pytest.mark.timeout(5)
    def test_describe_tool_structure_with_no_docstrings_or_params(self): # Removed @patch
        tool_name = "minimal_tool"
        mock_structure = {
            "filepath": f"dummy/tools/{tool_name}.py",
            "classes": [{"name": "MinimalTool", "docstring": None, "methods": [
                {"name": "run", "docstring": None, "parameters": [], "returns": None}
            ]}],
            "functions": []
        }
        self.mock_lwm_instance.get_tool_structure.return_value = mock_structure
        result = self.tool.execute("describe_tool", tool_name=tool_name)
        self.assertIn("Class: MinimalTool", result)
        self.assertNotIn("Docstring:", result.split("Class: MinimalTool")[1].split("Methods:")[0]) # No class docstring
        self.assertIn("- run()", result) # Empty params
        self.assertNotIn("->", result.split("- run()")[1].split("\n")[0]) # No return type
        self.assertNotIn("Docstring:", result.split("- run()")[1]) # No method docstring

    @pytest.mark.timeout(5)
    def test_describe_tool_not_found(self):
        tool_name = "unknown_tool"
        self.mock_lwm_instance.get_tool_structure.return_value = None # LWM returns None if not found

        expected_output = f"Tool '{tool_name}' not found or could not be analyzed."
        result = self.tool.execute("describe_tool", tool_name=tool_name)

        self.assertEqual(result, expected_output)
        self.mock_lwm_instance.get_tool_structure.assert_called_once_with(tool_name)

    @pytest.mark.timeout(5)
    def test_execute_unknown_action(self):
        action = "non_existent_action"
        expected_output = f"Error: Unknown action '{action}' for CodeUnderstandingTool. Available actions: list_tools, describe_tool."
        result = self.tool.execute(action)
        self.assertEqual(result, expected_output)

    @pytest.mark.timeout(5)
    def test_execute_describe_tool_missing_tool_name(self):
        expected_output = "Error: 'tool_name' parameter is required for the 'describe_tool' action."
        result = self.tool.execute("describe_tool") # tool_name is None
        self.assertEqual(result, expected_output)

if __name__ == '__main__':
    unittest.main()
