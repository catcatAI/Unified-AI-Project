#!/usr/bin/env python3
"""
Start Angela AI backend and delegate the card game development document task to her.
This script only sets up the infrastructure — Angela herself processes the cards.
"""

import sys
import os
import json
import time
import subprocess
import signal
import socket
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_DIR = PROJECT_ROOT / "apps" / "backend"
BACKEND_SRC = BACKEND_DIR / "src"
CARD_DATA_DIR = PROJECT_ROOT / "data" / "card_pile_downloaded"
OUTPUT_DIR = Path(r"G:\我的雲端硬碟\卡片開發")

print("=" * 60)
print("🌟 Delegate Card Task to Angela AI")
print("=" * 60)

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"\n📁 Output directory: {OUTPUT_DIR}")

# Count downloaded cards
md_files = sorted(CARD_DATA_DIR.glob("*.md"))
print(f"📚 Available cards: {len(md_files)} files ({sum(f.stat().st_size for f in md_files)//1024} KB)")

# Start backend server
print("\n🚀 Starting Angela AI backend server...")
env = os.environ.copy()
env["PYTHONPATH"] = str(BACKEND_SRC) + os.pathsep + env.get("PYTHONPATH", "")

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "services.main_api_server:app",
     "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
    cwd=str(BACKEND_DIR),
    env=env,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Wait for server to be ready
print("   Waiting for server (up to 120s)...")
start = time.time()
ready = False
while time.time() - start < 120:
    if proc.poll() is not None:
        print(f"   ❌ Server process exited prematurely (code {proc.returncode})")
        sys.exit(1)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", 8000))
        sock.close()
        if result == 0:
            ready = True
            break
    except Exception:
        pass
    elapsed = int(time.time() - start)
    print(f"   ... {elapsed}s", end="\r")
    time.sleep(1)

if not ready:
    print("\n   ❌ Server failed to start within 120s")
    proc.kill()
    sys.exit(1)

print(f"\n   ✅ Server ready in {int(time.time()-start)}s!")

# Now send the task to Angela
# We need to feed Angela the card data. Since 72 docs is too much for one chat,
# we'll send a comprehensive overview + ask her to process them

print("\n📤 Sending task to Angela AI...")

# First: send the task description
task_message = f"""我有一個卡片遊戲的企劃，總共 72 份卡片文件已經下載到了本地資料夾：

{len(md_files)} 張卡片檔案位置：{CARD_DATA_DIR}

請你：
1. 先讀取所有卡片文件的內容（在 {CARD_DATA_DIR} 中）
2. 分類所有卡片（角色卡、組織卡、國家卡、規則卡、場景卡、事件卡、劇情卡等）
3. 檢查是否有遺漏、衝突、缺失欄位
4. 自動補充缺失的資訊
5. 整理成完整的卡片遊戲開發文件

開發文件請輸出到：{OUTPUT_DIR}

請先讀取所有卡片內容，然後一步步完成這個任務。做好後告訴我你發現了什麼。"""

# Send to Angela's chat API
import urllib.parse

data = json.dumps({
    "message": task_message,
    "session_id": "card_game_dev_session",
    "user_name": "玩家",
    "history": []
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/chat/unified",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        response = json.loads(resp.read().decode("utf-8"))
    print(f"\n✅ Angela responded!")
    print(f"   Response: {response.get('response_text', '')[:500]}")
    print(f"   Source: {response.get('source', 'N/A')}")
    print(f"   Emotion: {response.get('emotion', 'N/A')}")
except urllib.error.HTTPError as e:
    print(f"\n❌ HTTP Error: {e.code} {e.reason}")
    print(f"   Body: {e.read().decode('utf-8')[:300]}")
except Exception as e:
    print(f"\n❌ Error: {e}")

# Keep server running for Angela to continue processing
print(f"\n{'='*60}")
print(f"ℹ️  Backend server is still running on http://127.0.0.1:8000")
print(f"   Angela is processing the cards. You can interact with her at:")
print(f"   - Chat API: POST /chat/unified")
print(f"   - Card output: {OUTPUT_DIR}")
print(f"   Press Ctrl+C to stop the server when done.")
print(f"{'='*60}")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n\nShutting down Angela...")
    proc.terminate()
    proc.wait(timeout=5)
    print("Done.")
