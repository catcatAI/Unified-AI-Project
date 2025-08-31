import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from datetime import datetime, timezone
import uuid

def test_datetime_import():
    """Test that datetime can be used correctly"""
    try:
        now = datetime.now(timezone.utc).isoformat()
        print(f"DateTime test passed: {now}")
        return True
    except Exception as e:
        print(f"DateTime test failed: {e}")
        return False

def test_content_analyzer():
    """Test ContentAnalyzerModule initialization"""
    try:
        analyzer = ContentAnalyzerModule()
        print("ContentAnalyzerModule initialized successfully")
        return True
    except Exception as e:
        print(f"ContentAnalyzerModule initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("Running fix verification tests...")
    
    datetime_ok = test_datetime_import()
    analyzer_ok = test_content_analyzer()
    
    if datetime_ok and analyzer_ok:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed!")
        sys.exit(1)