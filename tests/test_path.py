"""
测试模块 - test_path

自动生成的测试模块,用于验证系统功能。
"""

import sys

# Print the current sys.path
print("Current sys.path:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

# Check if we can import apps:
try:
    import apps
    print("\nSuccessfully imported apps module")
    print(f"apps module location: {apps.__file__}")
except ImportError as e:
    print(f"\nFailed to import apps module: {e}")

# Check if we can import apps.backend:
try:
    from apps import backend
    print("\nSuccessfully imported apps.backend module")
    print(f"backend module location: {backend.__file__}")
except ImportError as e:
    print(f"\nFailed to import apps.backend module: {e}")

# Check if we can import apps.backend.src:
try:
    from apps.backend import src
    print("\nSuccessfully imported apps.backend.src module")
    print(f"src module location: {src.__file__}")
except ImportError as e:
    print(f"\nFailed to import apps.backend.src module: {e}")

# Check if we can import the specific module we need:
try:
    from hsp.connector import HSPConnector
    print("\nSuccessfully imported apps.backend.src.hsp.connector module")
    print(f"HSPConnector location: {HSPConnector.__module__}")
except ImportError as e:
    print(f"\nFailed to import apps.backend.src.hsp.connector module: {e}")