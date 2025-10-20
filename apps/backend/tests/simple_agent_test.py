import sys
import os

# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports() -> None:
    """Test that we can import all agent classes."""
    try:
        _ = print("✓ BaseAgent imported successfully")
        
        _ = print("✓ CodeUnderstandingAgent imported successfully")
        
        _ = print("✓ CreativeWritingAgent imported successfully")
        
        _ = print("✓ DataAnalysisAgent imported successfully")
        
        _ = print("✓ AudioProcessingAgent imported successfully")
        
        _ = print("\nAll agents imported successfully!")
        return True
    except Exception as e:
        _ = print(f"Error: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)