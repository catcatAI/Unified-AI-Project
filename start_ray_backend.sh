#!/bin/bash
cd /mnt/d/Projects/Unified-AI-Project/apps/backend

# 設定 Python 路徑，讓 Ray worker 能找到 'apps' 模組
export PYTHONPATH="/mnt/d/Projects/Unified-AI-Project:$PYTHONPATH"

# 啟動 Ray head node
ray start --head --num-cpus=1 --object-store-memory=200MB --include-dashboard=false

# 等待 Ray 啟動
sleep 3

# 啟動後端
python main.py
