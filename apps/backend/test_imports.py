import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")

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
    from src.services.multi_llm_service import MultiLLMService
    print("[OK] MultiLLMService imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import MultiLLMService: {e}")

print("Import test completed.")