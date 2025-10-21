import sys
import os

# 添加项目路径
project_root: str = r"D:\Projects\Unified-AI-Project"
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))
sys.path.insert(0, os.path.join(project_root, "apps", "backend"))
sys.path.insert(0, os.path.join(project_root, "apps", "backend", "src"))

print("Python path:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

# 检查是否可以导入关键模块
try:
    import pytest
    print(f"\nPytest version: {pytest.__version__}")
except ImportError as e:
    print(f"\nFailed to import pytest: {e}")

try:
    print("Successfully imported HSPConnector")
except ImportError as e:
    print(f"Failed to import HSPConnector: {e}")

try:
    print("Successfully imported MockMqttBroker")
except ImportError as e:
    print(f"Failed to import MockMqttBroker: {e}")

print("\nEnvironment check completed.")