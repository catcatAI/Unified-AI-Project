"""
Tiered Configuration Loader
Implements the Default -> User -> Angela priority chain.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional