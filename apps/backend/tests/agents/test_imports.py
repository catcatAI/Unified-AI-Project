import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_imports():
    """Test that we can import the necessary modules."""
    print("Starting import tests...")
    try:
        from agents.base_agent import BaseAgent
        print("BaseAgent imported successfully")
        
        from core_services import initialize_services, get_services, shutdown_services
        print("Core services imported successfully")
        
        from hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
        print("HSP types imported successfully")
        
        print("All imports successful!")
        return True
    except Exception as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    print(f"Test result: {success}")
    if not success:
        exit(1)