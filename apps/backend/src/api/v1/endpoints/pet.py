#!/usr/bin/env python3
"""
Desktop Pet API 端點
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any