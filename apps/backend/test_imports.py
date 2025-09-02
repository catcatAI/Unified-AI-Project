import sys
import os

# Use the path configuration from path_config.py
try:
    from apps.backend.src.path_config import PROJECT_ROOT
    sys.path.insert(0, str(PROJECT_ROOT / "apps" / "backend" / "src"))
except ImportError:
    # Fallback to default path handling
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
    from apps.backend.src.services.multi_llm_service import MultiLLMService
    print("[OK] MultiLLMService imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import MultiLLMService: {e}")

print("Import test completed.")