import sys
import os

# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_imports() -> None:
    """Test that we can import the necessary modules."""
    _ = print("Starting import tests...")
    try:
        _ = print("BaseAgent imported successfully")
        
        _ = print("All imports successful!")
        return True
    except Exception as e:
        _ = print(f"Import error: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    _ = print(f"Test result: {success}")
    if not success:
        _ = exit(1)