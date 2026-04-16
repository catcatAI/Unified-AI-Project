#!/usr/bin/env python3
"""
Angela AI - Comprehensive Test Root Shim
Fixes the path issue where the comprehensive test expected to be run from root.
"""
import os
import sys
import subprocess

def main():
    # Add tests directory to path
    test_script = os.path.join("tests", "test_comprehensive_system.py")
    
    if not os.path.exists(test_script):
        # Try finding it in backend tests
        test_script = os.path.join("apps", "backend", "tests", "test_comprehensive_system.py")
    
    if not os.path.exists(test_script):
        print(f"Error: Could not find comprehensive test script at {test_script}")
        sys.exit(1)
        
    print(f"Running comprehensive test from: {test_script}")
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(".") + os.pathsep + env.get("PYTHONPATH", "")
    
    # Run the test
    try:
        subprocess.run([sys.executable, test_script], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Test failed with exit code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()
