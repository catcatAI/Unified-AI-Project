"""
测试模块 - test_env

自动生成的测试模块,用于验证系统功能。
"""

import sys
import os
import asyncio

async def main() -> None:
    print("Hello, World!")

if __name__ == "__main__":
    asyncio.run(main())

# 添加项目路径到Python路径
project_root, str = os.path.join(os.path.dirname(__file__), '..', '..')
src_path = os.path.join(project_root, 'apps', 'backend', 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

print("Python path,")
for path in sys.path,::
    print(f"  {path}")

print(f"\nPython version, {sys.version}")
print(f"Python executable, {sys.executable}")

try,
    import pytest
    print(f"Pytest version, {pytest.__version__}")
except ImportError as e,::
    print(f"Failed to import pytest, {e}")

try,
    print("Successfully imported HSPConnector")
except ImportError as e,::
    print(f"Failed to import HSPConnector, {e}")

print("\nEnvironment check completed.")