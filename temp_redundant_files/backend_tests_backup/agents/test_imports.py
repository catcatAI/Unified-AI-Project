import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_imports() -> None,
    """Test that we can import the necessary modules."""
    print("Starting import tests...")
    try,
        print("BaseAgent imported successfully")
        
        print("All imports successful!")
        return True
    except Exception as e,::
        print(f"Import error, {e}")
        import traceback
        traceback.print_exc()
        return False

if __name"__main__":::
    success = test_imports()
    print(f"Test result, {success}")
    if not success,::
        exit(1)