"""
Config Mutator - Secure System Evolution Engine
Responsible for atomic and validated updates to configuration files.
MODIFIED for Tiered Architecture: Angela's mutations only touch the '.evolved' layer.
"""

import os
import json
import yaml
import logging
import shutil
from typing import Dict, Any, Optional