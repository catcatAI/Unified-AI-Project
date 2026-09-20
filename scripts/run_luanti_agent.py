#!/usr/bin/env python3
"""
Angela Luanti Game Agent Launcher

啟動 Luanti (Minetest) 遊戲自主代理（angela_agent）。
主系統（backend+desktop）請用 `python scripts/run_angela.py`（統一啟動器）。

Usage:
    python scripts/run_luanti_agent.py   # 啟動遊戲代理
"""

import sys
import os
import asyncio

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'apps', 'backend', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'apps', 'backend', 'src', 'integrations'))

from ai.autonomous.angela_agent import main

if __name__ == "__main__":
    asyncio.run(main())
