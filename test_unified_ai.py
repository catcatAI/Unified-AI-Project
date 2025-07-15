#!/usr/bin/env python3
"""
Unified AI System Test Script

This script tests the integrated math and logic models in the Unified AI Project.
"""

import os
import sys
import json

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from tools.math_model.lightweight_math_model import LightweightMathModel
from tools.logic_model.lightweight_logic_model import LightweightLogicModel

def test_math_model():
    """
    Test the lightweight math model.
    """
    print("=" * 50)
    print("TESTING MATH MODEL")
    print("=" * 50)
    
    model = LightweightMathModel()
    
    # Test basic arithmetic
    test_problems = [
        "What is 15 + 27?",
        "Calculate 8 * 9",
        "What is 100 - 37?",
        "Divide 84 by 12",
        "What is 2 to the power of 5?",
        "Solve: 3 + 4 * 2",
        "Calculate: (10 + 5) * 2"
    ]
    
    for problem in test_problems:
        result = model.solve_problem(problem)
        print(f"Problem: {problem}")
        print(f"Answer: {result}")
        print("-" * 30)
    
    return True

def test_logic_model():
    """
    Test the lightweight logic model.
    """
    print("\n" + "=" * 50)
    print("TESTING LOGIC MODEL")
    print("=" * 50)
    
    model = LightweightLogicModel()
    
    # Test basic logic
    test_propositions = [
        "true AND false",
        "true OR false",
        "NOT true",
        "NOT false",
        "(true AND false) OR true",
        "true AND (false OR true)",
        "NOT (true AND false)",
        "(true OR false) AND (true AND true)"
    ]
    
    for proposition in test_propositions:
        result = model.solve_problem(proposition)
        print(f"Proposition: {proposition}")
        print(f"Result: {result}")
        print("-" * 30)
    
    return True

def test_unified_problems():
    """
    Test problems that might require both math and logic reasoning.
    """
    print("\n" + "=" * 50)
    print("TESTING UNIFIED REASONING")
    print("=" * 50)
    
    math_model = LightweightMathModel()
    logic_model = LightweightLogicModel()
    
    # Test combined reasoning
    test_cases = [
        {
            "description": "Math then Logic: Is (5 + 3) greater than 7?",
            "math_part": "5 + 3",
            "logic_part": "8 > 7"
        },
        {
            "description": "Logic then Math: If true AND false is false, what is 10 * 0?",
            "logic_part": "true AND false",
            "math_part": "10 * 0"
        }
    ]
    
    for case in test_cases:
        print(f"Problem: {case['description']}")
        
        if 'math_part' in case:
            math_result = math_model.solve_problem(case['math_part'])
            print(f"Math calculation: {case['math_part']} = {math_result}")
        
        if 'logic_part' in case:
            logic_result = logic_model.solve_problem(case['logic_part'])
            print(f"Logic evaluation: {case['logic_part']} = {logic_result}")
        
        print("-" * 30)
    
    return True

def check_model_files():
    """
    Check if model files exist and are valid.
    """
    print("\n" + "=" * 50)
    print("CHECKING MODEL FILES")
    print("=" * 50)
    
    project_root = os.path.dirname(__file__)
    models_dir = os.path.join(project_root, "data", "models")
    
    model_files = [
        "lightweight_math_model.json",
        "lightweight_logic_model.json"
    ]
    
    for model_file in model_files:
        file_path = os.path.join(models_dir, model_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    model_data = json.load(f)
                print(f"✓ {model_file}: Valid JSON, {len(model_data)} keys")
            except json.JSONDecodeError:
                print(f"✗ {model_file}: Invalid JSON format")
        else:
            print(f"✗ {model_file}: File not found")
    
    return True

def check_datasets():
    """
    Check if datasets exist and show basic statistics.
    """
    print("\n" + "=" * 50)
    print("CHECKING DATASETS")
    print("=" * 50)
    
    project_root = os.path.dirname(__file__)
    datasets_dir = os.path.join(project_root, "data", "raw_datasets")
    
    dataset_files = [
        "arithmetic_train_dataset.json",
        "arithmetic_test_dataset.csv",
        "logic_train.json",
        "logic_test.json"
    ]
    
    for dataset_file in dataset_files:
        file_path = os.path.join(datasets_dir, dataset_file)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✓ {dataset_file}: {file_size:,} bytes")
            
            # Try to load and show sample count for JSON files
            if dataset_file.endswith('.json'):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        print(f"  → {len(data)} samples")
                        if len(data) > 0:
                            print(f"  → Sample: {data[0]}")
                except:
                    print(f"  → Could not parse JSON")
        else:
            print(f"✗ {dataset_file}: File not found")
    
    return True

def main():
    """
    Main test function.
    """
    print("UNIFIED AI SYSTEM TEST")
    print("=" * 60)
    print(f"Project Root: {os.path.dirname(__file__)}")
    print(f"Python Version: {sys.version}")
    print("=" * 60)
    
    try:
        # Check files first
        check_datasets()
        check_model_files()
        
        # Test individual models
        test_math_model()
        test_logic_model()
        
        # Test unified reasoning
        test_unified_problems()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)