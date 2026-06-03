"""
Angela AI v6.0 - Security & Communication Monitor
密鑰生成與加密通訊監控器

實現 A/B/C 密鑰體系：
- Key A: 後端控制密鑰 (Backend Control)
- Key B: 行動端通訊密鑰 (Mobile-Backend Comm)
- Key C: 桌面端/跨裝置同步密鑰 (Desktop/Sync)

包含系統匣監控功能，可常駐並啟停後端服務。
"""

import os
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional