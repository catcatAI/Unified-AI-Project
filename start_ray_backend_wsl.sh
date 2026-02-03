#!/bin/bash
# Unified AI Project - WSL2 Backend Launcher

set -e

echo "========================================"
echo "Unified AI Project - WSL2 Backend"
echo "========================================"

cd /mnt/d/Projects/Unified-AI-Project/apps/backend

source /mnt/d/Projects/Unified-AI-Project/myenv/bin/activate

export PYTHONPATH="/mnt/d/Projects/Unified-AI-Project:$PYTHONPATH"
echo "PYTHONPATH set"

ray stop 2>/dev/null || true
sleep 1

echo "Starting Ray..."
ray start --head --num-cpus=1 --object-store-memory=200MB --include-dashboard=false --disable-usage-stats

sleep 3

echo "Ray started:"
ray status 2>/dev/null || echo "Ray status check skipped"

echo ""
echo "Starting backend..."
python main.py
