"""
Configuration for pytest: Add project source directories to the Python path.
"""

import sys
import os
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "apps", "backend", "src")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
