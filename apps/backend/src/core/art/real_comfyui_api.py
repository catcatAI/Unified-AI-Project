"""
Angela Real Image Generator - ComfyUI API Integration
真实AI绘画模块 - 使用 ComfyUI API

使用前确保：
1. ComfyUI 运行在 http://127.0.0.1:8188
2. 安装了必要的模型 (SDXL/SD1.5)
"""

import asyncio
import aiohttp
import base64
import json
import time
from pathlib import Path
from typing import Optional, Dict, List