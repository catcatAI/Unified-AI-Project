import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

try:
    from src.services.main_api_server import app
    print("✓ Backend import: OK")
except Exception as e:
    print(f"✗ Backend import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.services.angela_llm_service import AngelaLLMService
    print("✓ LLM Service import: OK")
except Exception as e:
    print(f"✗ LLM Service import failed: {e}")

try:
    from src.core.autonomous.state_matrix import StateMatrix
    print("✓ State Matrix import: OK")
except Exception as e:
    print(f"✗ State Matrix import failed: {e}")

print("\n=== Environment Info ===")
print(f"Python: {sys.version}")
print(f"Working directory: {os.getcwd()}")
