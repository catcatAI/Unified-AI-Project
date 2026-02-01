#!/bin/bash
# Unified AI Project - WSL2 Complete Backend Launcher
# This script fixes ALL Ray issues and starts the full backend

set -e

echo "========================================"
echo "Unified AI Project - WSL2 Full Backend"
echo "========================================"

# 1. Navigate to project
echo "[1/5] Navigating to project..."
cd /mnt/d/Projects/Unified-AI-Project/apps/backend

# 2. Activate virtual environment
echo "[2/5] Activating virtual environment..."
source /mnt/d/Projects/Unified-AI-Project/myenv/bin/activate

# 3. Stop any existing Ray processes
echo "[3/5] Stopping existing Ray processes..."
ray stop 2>/dev/null || true
sleep 2

# 4. Set environment variables for Ray
export PYTHONPATH="/mnt/d/Projects/Unified-AI-Project:$PYTHONPATH"
export RAY_ADDRESS="auto"
export RAY_NUM_CPUS="1"
export RAY_OBJECT_STORE_MEMORY="200000000"  # 200MB in bytes
echo "[4/5] Environment configured:"
echo "   PYTHONPATH=$PYTHONPATH"

# 5. Start Ray and Backend together using a Python launcher
echo "[5/5] Starting Ray and Backend..."

# Create a combined launcher that initializes Ray correctly
python3 << 'PYTHON_EOF'
import os
import sys
import subprocess
import time

# Set environment
os.environ["PYTHONPATH"] = "/mnt/d/Projects/Unified-AI-Project:" + os.environ.get("PYTHONPATH", "")
os.environ["RAY_NUM_CPUS"] = "1"
os.environ["RAY_OBJECT_STORE_MEMORY"] = "200000000"
os.environ["RAY_DASHBOARD_IP"] = "127.0.0.1"

print("Environment set. Starting Ray...")

# Start Ray
result = subprocess.run(["ray", "start", "--head", "--num-cpus=1", 
                         "--object-store-memory=200000000", 
                         "--include-dashboard=false",
                         "--disable-usage-stats"],
                        capture_output=True, text=True)

if result.returncode != 0:
    print(f"Ray start warning: {result.stderr}")
else:
    print("Ray started successfully!")

# Wait for Ray to initialize
time.sleep(3)

# Start the backend
print("Starting backend...")
sys.path.insert(0, "/mnt/d/Projects/Unified-AI-Project/apps/backend")
exec(open("main.py").read())
PYTHON_EOF
