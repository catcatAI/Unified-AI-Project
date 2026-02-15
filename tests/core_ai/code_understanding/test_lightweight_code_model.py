"""
Tests for the LightweightCodeModel.
"""

import pytest
from unittest.mock import patch, mock_open
import os
import tempfile
import logging

from ai.code_understanding.lightweight_code_model import LightweightCodeModel

@pytest.fixture
def model_fixture():
    """Provides a LightweightCodeModel instance with a temporary tools directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        model = LightweightCodeModel(tools_directory=temp_dir)
        yield model, temp_dir

def _create_dummy_file(directory, filename, content=""): 
    filepath = os.path.join(directory, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)
    return filepath

def test_list_tool_files(model_fixture):
    """Test that tool files are listed correctly, including subdirectories and exclusions."""
    model, temp_dir = model_fixture
    
    _create_dummy_file(temp_dir, "tool_one.py")
    _create_dummy_file(temp_dir, "__init__.py")
    _create_dummy_file(temp_dir, "tool_dispatcher.py")
    _create_dummy_file(temp_dir, os.path.join("subdir", "tool_three.py"))
    _create_dummy_file(temp_dir, "data.txt")

    expected_files = sorted([
        os.path.join(temp_dir, "tool_one.py"),
        os.path.join(temp_dir, os.path.join("subdir", "tool_three.py"))
    ])
    
    tool_files = sorted(model.list_tool_files())
    
    assert tool_files == expected_files

def test_analyze_tool_file_simple(model_fixture):
    """Test analysis of a simple Python file with a class and function."""
    model, _ = model_fixture
    sample_code = """
class SimpleTool:
    def execute(self, value: int) -> str:
        return str(value)

def module_func(x: float):
    return x * 2
"""
    m = mock_open(read_data=sample_code)
    with patch("builtins.open", m):
        analysis_result = model.analyze_tool_file("dummy_path/simple_tool.py")

    assert analysis_result is not None
    assert analysis_result.filepath == "dummy_path/simple_tool.py"
    assert len(analysis_result.classes) == 1
    assert analysis_result.classes[0]["name"] == "SimpleTool"
    assert len(analysis_result.functions) == 1
    assert analysis_result.functions[0]["name"] == "module_func"

def test_analyze_tool_file_parsing_error(model_fixture, caplog):
    """Test that a file with syntax errors returns None and logs an error."""
    model, _ = model_fixture
    sample_code = "def func(a: int -> str:"
    m = mock_open(read_data=sample_code)
    with patch("builtins.open", m), caplog.at_level(logging.ERROR):
        analysis_result = model.analyze_tool_file("dummy_path/error_tool.py")
        assert analysis_result is None
        assert "Failed to parse" in caplog.text

def test_get_tool_structure_by_exact_name(model_fixture):
    """Test retrieving tool structure by an exact file name."""
    model, temp_dir = model_fixture
    _create_dummy_file(temp_dir, "my_exact_tool.py", "def run(): pass")

    with patch.object(model, 'analyze_tool_file') as mock_analyze:
        mock_analyze.return_value = {"name": "my_exact_tool"}
        result = model.get_tool_structure("my_exact_tool")
        mock_analyze.assert_called_once_with(os.path.join(temp_dir, "my_exact_tool.py"))
        assert result == {"name": "my_exact_tool"}

def test_get_tool_structure_ambiguous(model_fixture, caplog):
    """Test that an ambiguous tool name logs a warning and returns None."""
    model, temp_dir = model_fixture
    _create_dummy_file(temp_dir, "tool_ambiguous.py")
    _create_dummy_file(temp_dir, "ambiguous_tool.py")

    with caplog.at_level(logging.WARNING):
        result = model.get_tool_structure("ambiguous")
        assert result is None
        assert "Ambiguous tool name" in caplog.text
