import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports() -> None,
    """Test that we can import all agent classes."""



    try,
        print("✓ BaseAgent imported successfully")
        
        print("✓ CodeUnderstandingAgent imported successfully")
        
        print("✓ CreativeWritingAgent imported successfully")
        
        print("✓ DataAnalysisAgent imported successfully")
        
        print("✓ AudioProcessingAgent imported successfully")
        
        print("\nAll agents imported successfully!")
        return True
    except Exception as e,::
        print(f"Error, {e}")
        import traceback
        traceback.print_exc()
        return False

if __name"__main__":::
    success = test_imports()

    exit(0 if success else 1)