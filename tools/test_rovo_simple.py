#!/usr/bin/env python3
"""
Simple test script for Rovo Dev integration
"""

import sys
from pathlib import Path

def test_rovo_module():
    """Test that the rovo module can be imported"""
    print("Testing Rovo module import...")
    
    try:
        # Add the backend src directory to the path
        backend_src = Path(__file__).parent / "apps" / "backend" / "src"
        sys.path.insert(0, str(backend_src))
        
        # Try to import the rovo dev agent
        from integrations.rovo_dev_agent import RovoDevAgent
        print("Rovo module import test passed!")
        return True
    except Exception as e:
        print(f"Error during Rovo module import test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_connector():
    """Test that the enhanced connector can be imported"""
    print("Testing Enhanced connector import...")
    
    try:
        # Add the backend src directory to the path
        backend_src = Path(__file__).parent / "apps" / "backend" / "src"
        sys.path.insert(0, str(backend_src))
        
        # Try to import the enhanced connector
        from integrations.enhanced_rovo_dev_connector import EnhancedRovoDevConnector
        print("Enhanced connector import test passed!")
        return True
    except Exception as e:
        print(f"Error during Enhanced connector import test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Rovo Dev Simple Integration Test")
    print("=" * 35)
    print()
    
    # Run all tests
    try:
        # Add the backend src directory to the path
        backend_src = Path(__file__).parent / "apps" / "backend" / "src"
        sys.path.insert(0, str(backend_src))
        
        test1 = test_rovo_module()
        test2 = test_enhanced_connector()
        
        if test1 and test2:
            print("\nAll simple tests completed successfully!")
            return True
        else:
            print("\nSome simple tests failed!")
            return False
    except Exception as e:
        print(f"Error during simple testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)