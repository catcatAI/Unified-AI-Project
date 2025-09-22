import sys
import os

# 添加项目路径到 Python 路径
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_path)

print("Project path:", project_path)
print("Python path:", sys.path)

try:
    print("Importing src.services.main_api_server...")
    import apps.backend.src.services.main_api_server
    print("Import successful!")
    print("App instance:", src.services.main_api_server.app)
except Exception as e:
    print("Import failed:", e)
    import traceback
    traceback.print_exc()

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