"""
Test script to verify the upgraded LightweightCodeModel functionality.
"""

import pytest
import os

# Assuming the test is run from the project root, so imports should be relative to that.
from core_ai.code_understanding.lightweight_code_model import (
    LightweightCodeModel, CodeAnalysisResult
)

@pytest.fixture
def code_model():
    """Provides a LightweightCodeModel instance."""
    return LightweightCodeModel()

@pytest.fixture
def temp_test_file():
    """Creates a temporary python file for analysis and cleans it up afterward."""
    test_file_path = "test_temp_code.py"
    code_content = """

def simple_function():
    return 1

def complex_function(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
    else:
        while x < 0:
            x += 1
    return x

class TestClass:
    def method1(self):
        pass
    
    def method2(self, a, b):
        if a and b:
            return a + b
        return 0
"""
    with open(test_file_path, "w") as f:
        f.write(code_content)
    
    yield test_file_path
    
    if os.path.exists(test_file_path):
        os.remove(test_file_path)

def test_dna_chain_functionality(code_model: LightweightCodeModel):
    """Test DNA chain creation and retrieval."""
    chain = code_model.create_dna_chain("test_code_chain")
    chain.add_node("test_file_1.py")
    chain.add_node("test_file_2.py")
    
    retrieved_chain = code_model.get_dna_chain("test_code_chain")
    assert retrieved_chain is not None, "Failed to retrieve DNA chain"
    assert len(retrieved_chain.nodes) == 2, "Incorrect number of nodes in chain"

def test_code_complexity_calculation(code_model: LightweightCodeModel, temp_test_file: str):
    """Test code complexity calculation and analysis."""
    result = code_model.analyze_tool_file(temp_test_file, dna_chain_id="test_code_chain")
    
    assert result is not None, "Failed to analyze test file"
    assert isinstance(result, CodeAnalysisResult), "Result is not a CodeAnalysisResult instance"
    assert len(result.functions) == 2, "Incorrect number of functions detected"
    assert len(result.classes) == 1, "Incorrect number of classes detected"
    assert result.complexity_score > 0, "Complexity score should be positive"

    # Test analysis history
    history = code_model.get_analysis_history()
    assert len(history) > 0, "Analysis history should not be empty"

    # Test complexity cache
    complexity = code_model.get_code_complexity(temp_test_file)
    assert complexity is not None, "Complexity should be cached"
