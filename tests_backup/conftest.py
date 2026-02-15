"""
Configuration for pytest: Add project source directories to the Python path.
"""

import sys
import os

# Correctly identify the project root by navigating up from the conftest.py location
# Assuming conftest.py is in D:\Projects\Unified-AI-Project\tests
# We need to go up one level to reach D:\Projects\Unified-AI-Project
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_PATH = os.path.join(PROJECT_ROOT, "apps", "backend", "src")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# You can add other source directories if needed, for example:
# PACKAGES_PATH = os.path.join(PROJECT_ROOT, "packages")
# if PACKAGES_PATH not in sys.path:
#     sys.path.insert(0, PACKAGES_PATH)