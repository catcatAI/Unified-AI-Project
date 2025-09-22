import pytest
import os
from unittest.mock import patch, MagicMock
import unittest

# 修复导入路径
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from apps.backend.src.tools.code_understanding_tool import CodeUnderstandingTool
from apps.backend.src.ai.code_understanding.lightweight_code_model import CodeAnalysisResult

class TestCodeUnderstandingTool(unittest.TestCase):
    """Test cases for the CodeUnderstandingTool."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock LightweightCodeModel instance
        self.mock_lwm_instance = MagicMock()
        
        # Create an instance of CodeUnderstandingTool with the mock
        self.tool = CodeUnderstandingTool()
        self.tool.code_model = self.mock_lwm_instance

    @pytest.mark.timeout(5)
    def test_list_tools_success(self):
        # Configure the mock_lwm_instance (which is self.tool.code_model)
        mock_tool_files = [
            os.path.join("dummy/tools", "math_tool.py"), # Note: self.tool.tools_directory is not used by mock
            os.path.join("dummy/tools", "another_tool.py"),
            os.path.join("dummy/tools", "subdir", "sub_tool.py")
        ]
        # Create a mock for the code_model.list_tool_files method
        with patch.object(self.tool.code_model, 'list_tool_files', return_value=mock_tool_files):
            expected_output = "Available Python tools: another_tool, math_tool, sub_tool."
            result = self.tool.execute("list_tools")
            
            self.assertEqual(result, expected_output)

    @pytest.mark.timeout(5)
    def test_list_tools_no_tools_found(self):
        # Create a mock for the code_model.list_tool_files method
        with patch.object(self.tool.code_model, 'list_tool_files', return_value=[]):
            expected_output = "No Python tools found in the tools directory."
            result = self.tool.execute("list_tools")

            self.assertEqual(result, expected_output)

    @pytest.mark.timeout(5)
    def test_describe_tool_found(self): # Removed @patch('os.path.isfile')
        tool_name = "math_tool"

        mock_structure = {
            "filepath": f"dummy/tools/{tool_name}.py",
            "classes": [],
            "functions": [
                {
                    "name": "_load_math_model",
                    "docstring": "Loads the arithmetic model, handling potential TensorFlow import errors.",
                    "parameters": [],
                    "returns": None
                },
                {
                    "name": "extract_arithmetic_problem",
                    "docstring": "Extracts a basic arithmetic problem from a string.",
                    "parameters": [
                        {"name": "text", "annotation": "str", "default": None}
                    ],
                    "returns": "str | None"
                },
                {
                    "name": "calculate",
                    "docstring": "Takes a natural language string, extracts an arithmetic problem, and returns the calculated answer using the trained model.",
                    "parameters": [
                        {"name": "input_string", "annotation": "str", "default": None}
                    ],
                    "returns": "ToolDispatcherResponse"
                }
            ]
        }
        self.mock_lwm_instance.get_tool_structure.return_value = mock_structure

        result = self.tool.execute("describe_tool", tool_name=tool_name)

        self.assertIn(f"Description for tool '{tool_name}'", result)
        # Check for functions instead of classes since math_tool.py doesn't have classes
        self.assertIn("Function: _load_math_model", result)
        self.assertIn("Function: extract_arithmetic_problem", result)
        self.assertIn("Function: calculate", result)

    @pytest.mark.timeout(5)
    def test_describe_tool_not_found(self):
        tool_name = "unknown_tool"
        self.mock_lwm_instance.get_tool_structure.return_value = None # LWM returns None if not found
    
        expected_output = f"Tool '{tool_name}' not found or could not be analyzed."
        result = self.tool.execute("describe_tool", tool_name=tool_name)
    
        self.assertEqual(result, expected_output)

    @pytest.mark.timeout(5)
    def test_describe_tool_structure_with_no_docstrings_or_params(self): # Removed @patch
        tool_name = "minimal_tool"
        # Create a CodeAnalysisResult object instead of a dictionary
        mock_structure = CodeAnalysisResult(
            filepath=f"dummy/tools/{tool_name}.py",
            analysis_timestamp="2023-01-01",
            classes=[{"name": "MinimalTool", "docstring": None, "methods": [
                {"name": "run", "docstring": None, "parameters": [], "returns": None}
            ]}],
            functions=[],
            dependencies=[],
            complexity_score=0.0
        )
        self.mock_lwm_instance.get_tool_structure.return_value = mock_structure
        result = self.tool.execute("describe_tool", tool_name=tool_name)
        self.assertIn("Class: MinimalTool", result)

    @pytest.mark.timeout(5)
    def test_execute_unknown_action(self):
        result = self.tool.execute("unknown_action")
        self.assertIn("Error: Unknown action 'unknown_action'", result)

    @pytest.mark.timeout(5)
    def test_execute_describe_tool_missing_tool_name(self):
        result = self.tool.execute("describe_tool") # No tool_name provided
        self.assertIn("Error: 'tool_name' parameter is required", result)