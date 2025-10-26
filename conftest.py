"""
Configuration for pytest: Add project root to the Python path.
"""

import sys
import os

# Add the project root directory to the Python path to resolve import issues.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
