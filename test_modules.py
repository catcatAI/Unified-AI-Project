import sys
import os

# Add the src directory to the path
project_root = os.path.dirname(__file__)
backend_path = os.path.join(project_root, 'apps', 'backend')
src_path = os.path.join(backend_path, 'src')
sys.path.insert(0, src_path)
sys.path.insert(0, backend_path)

print("Testing module imports...")

try:
    import openai
    print("[OK] openai module imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import openai: {e}")

try:
    import msgpack
    print("[OK] msgpack module imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import msgpack: {e}")

try:
    from services.multi_llm_service import MultiLLMService
    print("[OK] MultiLLMService imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import MultiLLMService: {e}")

print("Module import test completed.")