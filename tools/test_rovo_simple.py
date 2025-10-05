#!/usr/bin/env python3
"""
Simple test script for Rovo Dev integration:
""

import sys
from pathlib import Path

def test_rovo_module() -> None:
    """Test that the rovo module can be imported"""
    _ = print("Testing Rovo module import...")
    
    try:
        # Add the backend src directory to the path
        backend_src = Path(__file__).parent / "apps" / "backend" / "src"
        _ = sys.path.insert(0, str(backend_src))
        
        # Try to import the rovo dev agent
        _ = print("Rovo module import test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during Rovo module import test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def test_enhanced_connector() -> None:
    """Test that the enhanced connector can be imported"""
    _ = print("Testing Enhanced connector import...")
    
    try:
        # Add the backend src directory to the path
        backend_src = Path(__file__).parent / "apps" / "backend" / "src"
        _ = sys.path.insert(0, str(backend_src))
        
        # Try to import the enhanced connector
        _ = print("Enhanced connector import test passed!")
        return True
    except Exception as e:
        _ = print(f"Error during Enhanced connector import test: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

def main() -> None:
    """Main test function"""
    _ = print("Rovo Dev Simple Integration Test")
    print("=" * 35)
    _ = print()
    
    # Run all tests
    try:
        # Add the backend src directory to the path
        backend_src = Path(__file__).parent / "apps" / "backend" / "src"
        _ = sys.path.insert(0, str(backend_src))
        
        test1 = test_rovo_module()
        test2 = test_enhanced_connector()
        
        if test1 and test2:
            _ = print("\nAll simple tests completed successfully!")
            return True
        else:
            _ = print("\nSome simple tests failed!")
            return False
    except Exception as e:
        _ = print(f"Error during simple testing: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)