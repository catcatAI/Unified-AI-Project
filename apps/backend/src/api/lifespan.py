"""
ANGELA-MATRIX: [L4-L5] [βδ] [A] [L3]
Application lifecycle management — startup/shutdown + service factories.
Extracted from main_api_server.py (A3 god module split).
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
