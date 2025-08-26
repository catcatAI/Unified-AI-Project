#!/usr/bin/env python3
"""
Test script to verify the upgraded LightweightCodeModel functionality
"""

import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
backend_path = os.path.join(project_root, 'apps', 'backend')
sys.path.insert(0, backend_path)

def test_lightweight_code_model_upgrade():
    """Test the upgraded LightweightCodeModel functionality."""
    print("Testing upgraded LightweightCodeModel...")
    
    try:
        # Import the upgraded model
        from src.core_ai.code_understanding.lightweight_code_model import (
            LightweightCodeModel, CodeAnalysisResult
        )
        
        # Create a model instance
        model = LightweightCodeModel()
        
        print("✓ Model class imported successfully")
        
        # Test DNA chain functionality
        print("\n--- Testing DNA Chain Functionality ---")
        chain = model.create_dna_chain("test_code_chain")
        chain.add_node("test_file_1.py")
        chain.add_node("test_file_2.py")
        
        retrieved_chain = model.get_dna_chain("test_code_chain")
        assert retrieved_chain is not None, "Failed to retrieve DNA chain"
        assert len(retrieved_chain.nodes) == 2, "Incorrect number of nodes in chain"
        print("✓ DNA chain functionality working")
        
        # Test code complexity calculation with a simple example
        print("\n--- Testing Code Complexity Calculation ---")
        
        # Create a temporary test file
        test_file_path = "test_temp_code.py"
        with open(test_file_path, "w") as f:
            f.write("""
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
""")
        
        # Analyze the test file
        result = model.analyze_tool_file(test_file_path, dna_chain_id="test_code_chain")
        
        assert result is not None, "Failed to analyze test file"
        assert isinstance(result, CodeAnalysisResult), "Result is not CodeAnalysisResult"
        assert len(result.functions) == 2, "Incorrect number of functions detected"
        assert len(result.classes) == 1, "Incorrect number of classes detected"
        assert result.complexity_score > 0, "Complexity score should be positive"
        
        print(f"✓ Code analysis working - Functions: {len(result.functions)}, Classes: {len(result.classes)}")
        print(f"✓ Complexity score: {result.complexity_score}")
        print(f"✓ Dependencies found: {len(result.dependencies)}")
        
        # Test analysis history
        history = model.get_analysis_history()
        assert len(history) > 0, "Analysis history should not be empty"
        print("✓ Analysis history tracking working")
        
        # Test complexity cache
        complexity = model.get_code_complexity(test_file_path)
        assert complexity is not None, "Complexity should be cached"
        print("✓ Complexity caching working")
        
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
        
        print("\n🎉 All tests passed! LightweightCodeModel upgrade successful.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_lightweight_code_model_upgrade()
    sys.exit(0 if success else 1)