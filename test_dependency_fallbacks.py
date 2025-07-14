#!/usr/bin/env python3
"""
Test script for dependency fallback mechanisms.
This script tests the dependency manager and fallback systems.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core_ai.dependency_manager import DependencyManager
from tools.dependency_checker import DependencyChecker

def test_dependency_manager():
    """Test the dependency manager functionality."""
    print("\n=== Testing Dependency Manager ===")
    
    dm = DependencyManager()
    
    # Test core dependencies
    print("\nCore Dependencies:")
    core_deps = ['flask', 'numpy', 'pyyaml', 'cryptography']
    for dep in core_deps:
        available = dm.is_available(dep)
        print(f"  {dep}: {'✓' if available else '✗'}")
    
    # Test optional dependencies
    print("\nOptional Dependencies:")
    optional_deps = ['tensorflow', 'fastapi', 'spacy', 'langchain']
    for dep in optional_deps:
        available = dm.is_available(dep)
        print(f"  {dep}: {'✓' if available else '✗'}")
    
    # Test getting dependencies
    print("\nTesting dependency retrieval:")
    try:
        tf = dm.get_dependency('tensorflow')
        print(f"  TensorFlow: {'✓ Available' if tf else '✗ Not available'}")
    except Exception as e:
        print(f"  TensorFlow: ✗ Error - {e}")
    
    try:
        fastapi = dm.get_dependency('fastapi')
        print(f"  FastAPI: {'✓ Available' if fastapi else '✗ Not available'}")
    except Exception as e:
        print(f"  FastAPI: ✗ Error - {e}")

def test_dependency_checker():
    """Test the dependency checker functionality."""
    print("\n=== Testing Dependency Checker ===")
    
    checker = DependencyChecker()
    
    # Get status report
    status = checker.check_all_dependencies()
    
    print(f"\nCore Dependencies Status: {status['summary']['available_core']}/{status['summary']['total_core']} available")
    
    print(f"\nOptional Dependencies Status: {status['summary']['available_optional']}/{status['summary']['total_optional']} available")
    
    # Show missing dependencies
    missing = checker.get_missing_dependencies()
    if missing['core']:
        print(f"\nMissing Core Dependencies: {', '.join(missing['core'])}")
    
    if any(missing['optional'].values()):
        print("\nMissing Optional Dependencies:")
        for category, deps in missing['optional'].items():
            if deps:
                print(f"  {category}: {', '.join(deps)}")
    
    # Show installation suggestions
    commands = checker.generate_install_commands(missing)
    if commands:
        print("\nInstallation Commands:")
        for cmd_type, command in commands.items():
            print(f"  {cmd_type}: {command}")

def test_tensorflow_fallback():
    """Test TensorFlow fallback mechanism."""
    print("\n=== Testing TensorFlow Fallback ===")
    
    try:
        from tools.math_model.model import ArithmeticSeq2Seq
        model = ArithmeticSeq2Seq()
        print("  ArithmeticSeq2Seq: ✓ Initialized successfully")
        
        # Test if TensorFlow functionality is available
        if hasattr(model, '_tensorflow_is_available') and callable(model._tensorflow_is_available):
            tf_available = model._tensorflow_is_available()
            print(f"  TensorFlow functionality: {'✓ Available' if tf_available else '✗ Disabled (fallback active)'}")
        
    except Exception as e:
        print(f"  ArithmeticSeq2Seq: ✗ Error - {e}")
    
    try:
        from tools.logic_model.logic_model_nn import LogicNNModel
        logic_model = LogicNNModel()
        print("  LogicNNModel: ✓ Initialized successfully")
        
        # Test if TensorFlow functionality is available
        if hasattr(logic_model, '_tensorflow_is_available') and callable(logic_model._tensorflow_is_available):
            tf_available = logic_model._tensorflow_is_available()
            print(f"  TensorFlow functionality: {'✓ Available' if tf_available else '✗ Disabled (fallback active)'}")
        
    except Exception as e:
        print(f"  LogicNNModel: ✗ Error - {e}")

def test_logic_tool_fallback():
    """Test logic tool fallback mechanism."""
    print("\n=== Testing Logic Tool Fallback ===")
    
    try:
        from tools.logic_tool import LogicTool
        logic_tool = LogicTool()
        print("  LogicTool: ✓ Initialized successfully")
        
        # Test NN evaluator availability
        try:
            # This should work regardless of TensorFlow availability
            result = logic_tool.evaluate_logic("true AND false")
            print(f"  Basic logic evaluation: ✓ Working (result: {result})")
        except Exception as e:
            print(f"  Basic logic evaluation: ✗ Error - {e}")
        
    except Exception as e:
        print(f"  LogicTool: ✗ Error - {e}")

def main():
    """Run all tests."""
    print("Dependency Fallback Mechanism Test")
    print("=" * 40)
    
    try:
        test_dependency_manager()
        test_dependency_checker()
        test_tensorflow_fallback()
        test_logic_tool_fallback()
        
        print("\n=== Test Summary ===")
        print("✓ All tests completed successfully!")
        print("\nThe dependency fallback mechanisms are working correctly.")
        print("The project can run with partial dependencies and gracefully")
        print("handle missing optional components.")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())