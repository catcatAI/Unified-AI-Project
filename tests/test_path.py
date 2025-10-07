"""
测试模块 - test_path

自动生成的测试模块，用于验证系统功能。
"""

import sys

# Print the current sys.path
_ = print("Current sys.path:")
for i, path in enumerate(sys.path):
    _ = print(f"  {i}: {path}")

# Check if we can import apps:
try:
    import apps
    _ = print("\nSuccessfully imported apps module")
    _ = print(f"apps module location: {apps.__file__}")
except ImportError as e:
    _ = print(f"\nFailed to import apps module: {e}")

# Check if we can import apps.backend:
try:
    from apps import backend
    _ = print("\nSuccessfully imported apps.backend module")
    _ = print(f"backend module location: {backend.__file__}")
except ImportError as e:
    _ = print(f"\nFailed to import apps.backend module: {e}")

# Check if we can import apps.backend.src:
try:
    from apps.backend import src
    _ = print("\nSuccessfully imported apps.backend.src module")
    _ = print(f"src module location: {src.__file__}")
except ImportError as e:
    _ = print(f"\nFailed to import apps.backend.src module: {e}")

# Check if we can import the specific module we need:
try:
    from apps.backend.src.hsp.connector import HSPConnector
    _ = print("\nSuccessfully imported apps.backend.src.hsp.connector module")
    _ = print(f"HSPConnector location: {HSPConnector.__module__}")
except ImportError as e:
    _ = print(f"\nFailed to import apps.backend.src.hsp.connector module: {e}")