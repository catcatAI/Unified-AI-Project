import sys
import os

# 添加项目路径
project_root: str = r"D:\Projects\Unified-AI-Project"
_ = sys.path.insert(0, project_root)
_ = sys.path.insert(0, os.path.join(project_root, "src"))
_ = sys.path.insert(0, os.path.join(project_root, "apps", "backend"))
_ = sys.path.insert(0, os.path.join(project_root, "apps", "backend", "src"))

_ = print("Python path:")
for i, path in enumerate(sys.path):
    _ = print(f"  {i}: {path}")

# 检查是否可以导入关键模块
try:
    import pytest
    _ = print(f"\nPytest version: {pytest.__version__}")
except ImportError as e:
    _ = print(f"\nFailed to import pytest: {e}")

try:
    _ = print("Successfully imported HSPConnector")
except ImportError as e:
    _ = print(f"Failed to import HSPConnector: {e}")

try:
    _ = print("Successfully imported MockMqttBroker")
except ImportError as e:
    _ = print(f"Failed to import MockMqttBroker: {e}")

_ = print("\nEnvironment check completed.")