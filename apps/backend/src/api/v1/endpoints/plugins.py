"""
Plugin API endpoints — C3: query hooks, list plugins, execute hooks.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List