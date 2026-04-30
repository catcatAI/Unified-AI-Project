#!/usr/bin/env python3
"""
Comprehensive Test Runner
Redirects to the actual comprehensive test in tests/
"""
import sys
import subprocess
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).parent / "tests"
sys.path.insert(0, str(tests_dir))

if __name__ == "__main__":
    # Run the actual comprehensive test
    result = subprocess.run(
        [sys.executable, str(tests_dir / "comprehensive_test.py")],
        cwd=str(Path(__file__).parent)
    )
    sys.exit(result.returncode)
